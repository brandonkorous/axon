// Axon Runner Host — manages worker runner processes on the host machine.
//
// Watches orgs/{org}/runners/{agent}/state.json for desired state changes
// written by the Axon backend (running in Docker). Spawns and stops runner
// subprocesses locally where Claude CLI and codebases are accessible.
//
// Usage:
//     node runner_host.js [ORGS_DIR]
//
//     ORGS_DIR defaults to the AXON_ORGS_DIR environment variable, or ./orgs

const fs = require("fs");
const path = require("path");
const { spawn, execSync } = require("child_process");

const POLL_INTERVAL = 3000; // ms
const MAX_LOG_BYTES = 1_000_000; // 1 MB
const STOP_TIMEOUT = 20_000; // ms
const KILL_TIMEOUT = 5_000; // ms

// ── Process tracking ──────────────────────────────────────────────

/** @type {Map<string, import("child_process").ChildProcess>} */
const processes = new Map(); // "org/agent" → ChildProcess
/** @type {Map<string, number>} */
const logHandles = new Map(); // "org/agent" → fd
let shuttingDown = false;

// ── Logging ───────────────────────────────────────────────────────

function timestamp() {
  const d = new Date();
  const hh = String(d.getHours()).padStart(2, "0");
  const mm = String(d.getMinutes()).padStart(2, "0");
  const ss = String(d.getSeconds()).padStart(2, "0");
  return `${hh}:${mm}:${ss}`;
}

function log(level, msg) {
  console.log(`${timestamp()} [${level}] ${msg}`);
}

// ── Helpers ───────────────────────────────────────────────────────

function readDesiredState(runnerDir) {
  const statePath = path.join(runnerDir, "state.json");
  try {
    const raw = fs.readFileSync(statePath, "utf-8");
    const data = JSON.parse(raw);
    return data.state || "stopped";
  } catch {
    return "stopped";
  }
}

function writeStatus(runnerDir, status) {
  const statusPath = path.join(runnerDir, "status.json");
  fs.writeFileSync(statusPath, JSON.stringify({ status }), "utf-8");
}

function truncateLog(logPath) {
  try {
    const stat = fs.statSync(logPath);
    if (stat.size <= MAX_LOG_BYTES) return;
    const data = fs.readFileSync(logPath);
    const halfway = Math.floor(data.length / 2);
    const idx = data.indexOf(0x0a, halfway); // newline
    if (idx === -1) return;
    fs.writeFileSync(logPath, data.subarray(idx + 1));
  } catch {
    // ignore
  }
}

function buildEnv() {
  const env = { ...process.env };
  if (process.platform === "win32") {
    const appdata = env.APPDATA || "";
    if (appdata) {
      const npmBin = path.join(appdata, "npm");
      if (!env.PATH || !env.PATH.includes(npmBin)) {
        env.PATH = npmBin + path.delimiter + (env.PATH || "");
      }
    }
  } else {
    const extras = ["/usr/local/bin", "/usr/bin"];
    for (const p of extras) {
      if (!env.PATH || !env.PATH.includes(p)) {
        env.PATH = (env.PATH || "") + path.delimiter + p;
      }
    }
  }
  return env;
}

function ensureDeps(runnerDir) {
  const pkgPath = path.join(runnerDir, "package.json");
  const modulesDir = path.join(runnerDir, "node_modules");
  if (!fs.existsSync(pkgPath) || fs.existsSync(modulesDir)) return;

  log("INFO", `Installing dependencies in ${runnerDir}...`);
  try {
    execSync("npm install --production --no-fund --no-audit", {
      cwd: runnerDir,
      stdio: ["ignore", "pipe", "pipe"],
      timeout: 120_000,
      env: buildEnv(),
    });
    log("INFO", "Dependencies installed");
  } catch (err) {
    log("ERROR", `npm install failed: ${err.message}`);
  }
}

function readConfig(runnerDir) {
  try {
    const raw = fs.readFileSync(path.join(runnerDir, "config.json"), "utf-8");
    return JSON.parse(raw);
  } catch {
    return {};
  }
}

function isSandboxed(runnerDir) {
  const config = readConfig(runnerDir);
  return config.sandbox?.enabled === true;
}

function startSandboxRunner(key, runnerDir) {
  const config = readConfig(runnerDir);
  const sandbox = config.sandbox || {};
  const resources = sandbox.resources || {};
  const network = sandbox.network || {};
  const image = sandbox.image || "axon-sandbox:latest";
  const containerName = `axon-sandbox-${key.replace("/", "-")}`;
  const codebase = config.codebase || runnerDir;

  const logPath = path.join(runnerDir, "runner.log");
  truncateLog(logPath);
  const logFd = fs.openSync(logPath, "a");

  // Build docker run args
  const args = [
    "run", "--rm",
    "--name", containerName,
    "--label", `axon.sandbox.key=${key}`,
    "-v", `${runnerDir}:/runner`,
    "-v", `${codebase}:/workspace`,
  ];

  // Resource limits
  if (resources.cpu_count) args.push("--cpus", String(resources.cpu_count));
  if (resources.memory_mb) args.push("--memory", `${resources.memory_mb}m`);
  if (resources.pids_limit) args.push("--pids-limit", String(resources.pids_limit));

  // Network
  if (network.enabled === false) {
    args.push("--network", "none");
  }

  // Add host.docker.internal for backend access
  if (process.platform !== "linux") {
    // Docker Desktop already provides this; Linux needs --add-host
  } else {
    args.push("--add-host", "host.docker.internal:host-gateway");
  }

  args.push(image);

  const child = spawn("docker", args, {
    cwd: runnerDir,
    stdio: ["ignore", logFd, logFd],
    env: buildEnv(),
  });

  processes.set(key, child);
  logHandles.set(key, logFd);
  writeStatus(runnerDir, "running");
  log("INFO", `Started sandbox ${key} (container=${containerName}, pid=${child.pid})`);
}

function startRunner(key, runnerDir) {
  const runnerScript = path.join(runnerDir, "runner.js");
  if (!fs.existsSync(runnerScript)) {
    log("WARN", `No runner.js in ${runnerDir} — skipping`);
    return;
  }

  // Use sandbox mode if configured
  if (isSandboxed(runnerDir)) {
    startSandboxRunner(key, runnerDir);
    return;
  }

  ensureDeps(runnerDir);

  const logPath = path.join(runnerDir, "runner.log");
  truncateLog(logPath);

  const logFd = fs.openSync(logPath, "a");
  const env = buildEnv();

  const child = spawn(process.execPath, ["runner.js"], {
    cwd: runnerDir,
    stdio: ["ignore", logFd, logFd],
    env,
  });

  processes.set(key, child);
  logHandles.set(key, logFd);
  writeStatus(runnerDir, "running");
  log("INFO", `Started ${key} (pid=${child.pid})`);
}

function stopRunner(key, runnerDir) {
  const proc = processes.get(key);
  if (!proc) return;

  return new Promise((resolve) => {
    let settled = false;

    const onExit = () => {
      if (settled) return;
      settled = true;
      cleanupProcess(key, runnerDir);
      log("INFO", `Stopped ${key}`);
      resolve();
    };

    // Runner reads state.json=stop and exits on its own
    proc.once("exit", onExit);

    // If it doesn't exit in time, terminate
    const timer = setTimeout(() => {
      if (settled) return;
      log("WARN", `${key} did not exit cleanly — terminating`);
      proc.kill("SIGTERM");

      const killTimer = setTimeout(() => {
        if (settled) return;
        proc.kill("SIGKILL");
      }, KILL_TIMEOUT);

      proc.once("exit", () => {
        clearTimeout(killTimer);
        onExit();
      });
    }, STOP_TIMEOUT);

    // If it exits before timeout, clear the timer
    proc.once("exit", () => clearTimeout(timer));
  });
}

function cleanupProcess(key, runnerDir) {
  processes.delete(key);
  const fd = logHandles.get(key);
  if (fd !== undefined) {
    try { fs.closeSync(fd); } catch { /* ignore */ }
    logHandles.delete(key);
  }
  writeStatus(runnerDir, "stopped");

  const pidFile = path.join(runnerDir, "runner.pid");
  try { fs.unlinkSync(pidFile); } catch { /* ignore */ }
}

// ── Scan loop ─────────────────────────────────────────────────────

async function scanRunners(orgsDir) {
  let orgEntries;
  try { orgEntries = fs.readdirSync(orgsDir, { withFileTypes: true }); } catch { return; }

  for (const orgEntry of orgEntries) {
    if (!orgEntry.isDirectory()) continue;
    const runnersDir = path.join(orgsDir, orgEntry.name, "runners");
    let runnerEntries;
    try { runnerEntries = fs.readdirSync(runnersDir, { withFileTypes: true }); } catch { continue; }

    for (const runnerEntry of runnerEntries) {
      if (!runnerEntry.isDirectory()) continue;
      const runnerDir = path.join(runnersDir, runnerEntry.name);
      const key = `${orgEntry.name}/${runnerEntry.name}`;
      const desired = readDesiredState(runnerDir);
      const proc = processes.get(key);
      let isAlive = proc != null && !proc.killed && proc.exitCode === null;

      // Handle unexpected death
      if (proc && !isAlive) {
        log("WARN", `${key} exited unexpectedly (code=${proc.exitCode})`);
        cleanupProcess(key, runnerDir);
        isAlive = false;
      }

      // Reconcile desired vs actual
      if (desired === "running" && !isAlive) {
        startRunner(key, runnerDir);
      } else if ((desired === "stop" || desired === "stopped") && isAlive) {
        await stopRunner(key, runnerDir);
      } else if (desired === "paused" && !isAlive) {
        writeStatus(runnerDir, "stopped");
      } else if (desired === "paused" && isAlive) {
        writeStatus(runnerDir, "paused");
      } else if (desired === "running" && isAlive) {
        writeStatus(runnerDir, "running");
      }
    }
  }
}

// ── Shutdown ──────────────────────────────────────────────────────

function shutdownAll() {
  if (shuttingDown) return;
  shuttingDown = true;
  log("INFO", `Shutting down ${processes.size} runner(s)...`);

  const kills = [];
  for (const [key, proc] of processes) {
    if (proc.exitCode === null) {
      proc.kill("SIGTERM");
      kills.push(
        new Promise((resolve) => {
          const timer = setTimeout(() => { proc.kill("SIGKILL"); resolve(); }, KILL_TIMEOUT);
          proc.once("exit", () => { clearTimeout(timer); resolve(); });
        })
      );
    }
  }

  Promise.all(kills).then(() => {
    for (const fd of logHandles.values()) {
      try { fs.closeSync(fd); } catch { /* ignore */ }
    }
    processes.clear();
    logHandles.clear();
    process.exit(0);
  });
}

// ── Main ──────────────────────────────────────────────────────────

async function main() {
  const arg = process.argv[2] || process.env.AXON_ORGS_DIR || "./orgs";
  const orgsDir = path.resolve(arg);

  if (!fs.existsSync(orgsDir) || !fs.statSync(orgsDir).isDirectory()) {
    log("ERROR", `Orgs directory not found: ${orgsDir}`);
    process.exit(1);
  }

  log("INFO", "Axon Runner Host started");
  log("INFO", `Watching: ${orgsDir}`);
  log("INFO", `Poll interval: ${POLL_INTERVAL / 1000}s`);

  process.on("SIGINT", shutdownAll);
  process.on("SIGTERM", shutdownAll);

  while (!shuttingDown) {
    try {
      await scanRunners(orgsDir);
    } catch (err) {
      log("ERROR", `Error during scan: ${err.message}`);
    }
    await new Promise((r) => setTimeout(r, POLL_INTERVAL));
  }
}

main();
