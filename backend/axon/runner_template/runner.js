/**
 * Axon Worker Runner — self-contained, zero-dependency agent runner.
 * Reads configuration from config.json in the same directory.
 * Controlled via state.json written by the Axon backend process manager.
 */
const fs = require("fs");
const path = require("path");

const POLL_INTERVAL = 15_000;
const RUNNER_DIR = __dirname;

function log(level, msg) {
  console.log(`${new Date().toTimeString().slice(0, 8)} [${level}] ${msg}`);
}

// ── Bridge loader ────────────────────────────────────────────────

const BRIDGE_MAP = {
  code: "./code_bridge",
  documents: "./documents_bridge",
  email: "./email_bridge",
  images: "./images_bridge",
  browser: "./browser_bridge",
  shell: "./shell_bridge",
};

function loadBridge(workerType) {
  const mod = BRIDGE_MAP[workerType] || "./code_bridge";
  log("INFO", `Loading bridge: ${mod} (worker_type=${workerType || "code"})`);
  const bridge = require(mod);

  if (typeof bridge.generatePlan !== "function")
    throw new Error(`Bridge ${mod} missing generatePlan()`);
  if (typeof bridge.executePlan !== "function")
    throw new Error(`Bridge ${mod} missing executePlan()`);

  if (bridge.meta) {
    log("INFO", `Bridge: ${bridge.meta.name} — ${bridge.meta.description}`);
    if (bridge.meta.capabilities.length)
      log("INFO", `Capabilities: ${bridge.meta.capabilities.join(", ")}`);
  }

  return bridge;
}

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

// ── HTTP helpers (Node 18+ fetch) ───────────────────────────────

async function httpGet(url) {
  const resp = await fetch(url, { signal: AbortSignal.timeout(30_000) });
  if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
  return resp.json();
}

async function httpPost(url, data) {
  try {
    const resp = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
      signal: AbortSignal.timeout(300_000),
    });
    return { statusCode: resp.status, body: await resp.json() };
  } catch (err) {
    return { statusCode: 0, body: { error: err.message } };
  }
}

// ── Config & state ──────────────────────────────────────────────

function loadConfig() {
  return JSON.parse(fs.readFileSync(path.join(RUNNER_DIR, "config.json"), "utf-8"));
}

function readState() {
  try {
    return JSON.parse(fs.readFileSync(path.join(RUNNER_DIR, "state.json"), "utf-8")).state || "running";
  } catch (_) { return "running"; }
}

function writePid() {
  fs.writeFileSync(path.join(RUNNER_DIR, "runner.pid"), String(process.pid), "utf-8");
}

function removePid() {
  try { fs.unlinkSync(path.join(RUNNER_DIR, "runner.pid")); } catch (_) {}
}

// ── Runner ──────────────────────────────────────────────────────

class Runner {
  constructor(config) {
    const base = config.axon_url.replace(/\/+$/, "");
    this.base = `${base}/api/orgs/${config.org_id}/external/${config.agent_id}`;
    this.workDir = config.codebase || config.working_directory || ".";
    this._busy = false;
    this._shutdown = false;

    const bridge = loadBridge(config.worker_type);
    this._generatePlan = bridge.generatePlan;
    this._executePlan = bridge.executePlan;
  }

  async run() {
    log("INFO", `Runner started — polling ${this.base} every ${POLL_INTERVAL / 1000}s`);
    log("INFO", `Working directory: ${this.workDir}`);

    while (!this._shutdown) {
      const state = readState();
      if (state === "stop") { log("INFO", "Stop signal received — shutting down"); break; }
      if (state === "paused") { await sleep(POLL_INTERVAL); continue; }

      try {
        await this._tick();
      } catch (err) {
        const msg = err?.cause?.code === "ECONNREFUSED"
          ? `Cannot reach Axon — retrying in ${POLL_INTERVAL / 1000}s`
          : `Unexpected error in tick: ${err.message || err}`;
        log(err?.cause?.code === "ECONNREFUSED" ? "WARN" : "ERROR", msg);
      }
      await sleep(POLL_INTERVAL);
    }
  }

  async _tick() {
    const data = await httpGet(`${this.base}/tasks`);
    for (const task of data.tasks || []) {
      if (!task.path) continue;
      if (task.status === "pending") await this._handlePending(task);
      else if (task.status === "approved") await this._handleApproved(task);
    }
  }

  async _reportActivity(phase, taskName = "", detail = "") {
    try {
      await httpPost(`${this.base}/activity`, { phase, task_name: taskName, detail });
    } catch (_) { /* best-effort */ }
  }

  async _handlePending(task) {
    if (this._busy) return;
    this._busy = true;
    try {
      const { path: taskPath, name = taskPath, body = "" } = task;
      log("INFO", `New task: ${name}`);
      await this._reportActivity("generating_plan", name);

      let plan;
      try {
        plan = await this._generatePlan(this.workDir, `${name}\n\n${body}`);
      } catch (err) {
        log("ERROR", `Plan generation failed: ${err.message}`);
        await this._submitResult(taskPath, false, String(err), "", String(err));
        await this._reportActivity("idle");
        return;
      }

      log("INFO", `Submitting plan for approval: ${taskPath}`);
      await this._reportActivity("awaiting_approval", name);
      const { statusCode, body: resp } = await httpPost(
        `${this.base}/tasks/${taskPath}/plan`, { plan, files_affected: [] }
      );
      log(statusCode === 200 ? "INFO" : "ERROR",
        statusCode === 200 ? "Plan submitted — awaiting user approval" : `Plan submission failed: ${JSON.stringify(resp)}`);
    } finally { this._busy = false; }
  }

  async _handleApproved(task) {
    if (this._busy) return;
    this._busy = true;
    try {
      const { path: taskPath, plan_content: plan = "", name = taskPath } = task;
      if (!plan) { log("WARN", `Approved task has no plan content: ${taskPath}`); return; }

      log("INFO", `Executing approved plan: ${name}`);
      await this._reportActivity("executing", name);
      let result;
      try {
        result = await this._executePlan(this.workDir, plan);
      } catch (err) {
        log("ERROR", `Execution failed: ${err.message}`);
        await this._submitResult(taskPath, false, String(err), "", String(err));
        await this._reportActivity("idle");
        return;
      }

      await this._submitResult(taskPath, result.success, result.output.slice(0, 2000), result.diff || "", result.error);
      log("INFO", `Task ${result.success ? "done" : "failed"}: ${name}`);
      await this._reportActivity("idle");
    } finally { this._busy = false; }
  }

  async _submitResult(taskPath, success, summary, diff = "", error = null) {
    const { statusCode, body: resp } = await httpPost(
      `${this.base}/tasks/${taskPath}/result`, { success, summary, diff, error }
    );
    if (statusCode !== 200) log("ERROR", `Result submission failed: ${JSON.stringify(resp)}`);
  }

  stop() { this._shutdown = true; }
}

// ── Main ────────────────────────────────────────────────────────

async function main() {
  const config = loadConfig();
  writePid();
  const runner = new Runner(config);

  const shutdown = () => { log("INFO", "Shutting down"); runner.stop(); };
  process.on("SIGTERM", shutdown);
  process.on("SIGINT", shutdown);

  try { await runner.run(); } finally { removePid(); }
}

main().catch((err) => {
  log("ERROR", `Fatal: ${err.message || err}`);
  removePid();
  process.exit(1);
});
