import http from "node:http";
import { spawn } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const SERVER_SCRIPT = path.join(__dirname, "server.js");
const MANAGER_PORT = parseInt(process.env.HOST_AGENT_MANAGER_PORT || "9099", 10);
const MAX_RESTARTS = 3;
const RESTART_WINDOW_MS = 60_000;
const KILL_TIMEOUT_MS = 5_000;
const LOG_LINES = 100;
const IS_WIN = process.platform === "win32";

const agents = new Map(); // id -> { process, config, status, pid, restarts, restartTimestamps, logs }

function json(res, status, data) {
  res.writeHead(status, { "Content-Type": "application/json" });
  res.end(JSON.stringify(data));
}

function readBody(req) {
  return new Promise((resolve, reject) => {
    const chunks = [];
    req.on("data", (c) => chunks.push(c));
    req.on("end", () => {
      try { resolve(JSON.parse(Buffer.concat(chunks).toString())); }
      catch { reject(new Error("Invalid JSON body")); }
    });
    req.on("error", reject);
  });
}

function pushLog(agent, line) {
  agent.logs.push(line);
  if (agent.logs.length > LOG_LINES) agent.logs.shift();
}

function startAgent(config) {
  const existing = agents.get(config.id);
  if (existing?.status === "running") {
    return { ok: false, error: `Agent "${config.id}" is already running` };
  }

  const args = [SERVER_SCRIPT, "--id", config.id, "--path", config.path, "--port", String(config.port)];
  if (config.executables?.length) args.push("--executables", config.executables.join(","));

  const child = spawn(process.execPath, args, { stdio: "pipe", windowsHide: true });

  const agent = {
    process: child,
    config,
    status: "running",
    pid: child.pid,
    restarts: existing?.restarts || 0,
    restartTimestamps: existing?.restartTimestamps || [],
    logs: existing?.logs || [],
  };

  child.stdout.on("data", (d) => d.toString().split("\n").filter(Boolean).forEach((l) => pushLog(agent, l)));
  child.stderr.on("data", (d) => d.toString().split("\n").filter(Boolean).forEach((l) => pushLog(agent, `[err] ${l}`)));

  child.on("exit", (code) => {
    if (agent.status === "stopped") return; // intentional stop
    agent.status = "crashed";
    agent.process = null;
    agent.pid = null;
    pushLog(agent, `Process exited with code ${code}`);

    // Auto-restart with rate limiting
    const now = Date.now();
    agent.restartTimestamps = agent.restartTimestamps.filter((t) => now - t < RESTART_WINDOW_MS);
    if (agent.restartTimestamps.length < MAX_RESTARTS) {
      agent.restartTimestamps.push(now);
      agent.restarts++;
      pushLog(agent, `Auto-restarting (attempt ${agent.restarts})...`);
      startAgent(agent.config);
    } else {
      pushLog(agent, `Max restarts (${MAX_RESTARTS}) reached within ${RESTART_WINDOW_MS / 1000}s window`);
    }
  });

  agents.set(config.id, agent);
  return { ok: true, pid: child.pid };
}

function stopAgent(id) {
  const agent = agents.get(id);
  if (!agent || agent.status !== "running" || !agent.process) {
    return { ok: false, error: `Agent "${id}" is not running` };
  }

  agent.status = "stopped";
  const child = agent.process;
  agent.process = null;
  agent.pid = null;
  agent.restartTimestamps = [];

  if (IS_WIN) {
    try { process.kill(child.pid); } catch { /* already dead */ }
  } else {
    child.kill("SIGTERM");
    setTimeout(() => {
      try { child.kill("SIGKILL"); } catch { /* already dead */ }
    }, KILL_TIMEOUT_MS);
  }

  return { ok: true };
}

// --- HTTP Router ---
const server = http.createServer(async (req, res) => {
  const url = new URL(req.url, `http://${req.headers.host}`);
  const route = `${req.method} ${url.pathname}`;

  try {
    if (route === "GET /status") {
      const result = {};
      for (const [id, a] of agents) {
        result[id] = { status: a.status, pid: a.pid, port: a.config.port, path: a.config.path };
      }
      return json(res, 200, { agents: result });
    }

    if (route === "GET /logs") {
      const id = url.searchParams.get("id");
      const agent = agents.get(id);
      if (!agent) return json(res, 404, { error: `Agent "${id}" not found` });
      return json(res, 200, { id, logs: agent.logs });
    }

    if (route === "POST /start") {
      const body = await readBody(req);
      if (!body.id || !body.path || !body.port) {
        return json(res, 400, { error: "Missing required fields: id, path, port" });
      }
      const result = startAgent(body);
      return json(res, result.ok ? 200 : 409, result);
    }

    if (route === "POST /stop") {
      const body = await readBody(req);
      if (!body.id) return json(res, 400, { error: "Missing required field: id" });
      const result = stopAgent(body.id);
      return json(res, result.ok ? 200 : 404, result);
    }

    if (route === "POST /restart") {
      const body = await readBody(req);
      if (!body.id || !body.path || !body.port) {
        return json(res, 400, { error: "Missing required fields: id, path, port" });
      }
      const existing = agents.get(body.id);
      if (existing?.status === "running") stopAgent(body.id);
      // Reset restart tracking for intentional restarts
      const agent = agents.get(body.id);
      if (agent) { agent.restarts = 0; agent.restartTimestamps = []; }
      const result = startAgent(body);
      return json(res, result.ok ? 200 : 500, result);
    }

    json(res, 404, { error: "Not found" });
  } catch (e) {
    json(res, 500, { error: e.message });
  }
});

// --- Graceful shutdown ---
function shutdown() {
  console.log("\nShutting down all agents...");
  for (const [id] of agents) stopAgent(id);
  server.close(() => process.exit(0));
  setTimeout(() => process.exit(1), KILL_TIMEOUT_MS + 1000);
}

process.on("SIGINT", shutdown);
process.on("SIGTERM", shutdown);

server.listen(MANAGER_PORT, "0.0.0.0", () => {
  console.log(`\n  Axon Host Agent Manager`);
  console.log(`  ────────────────────────────`);
  console.log(`  Port: ${MANAGER_PORT}`);
  console.log(`  ────────────────────────────\n`);
});
