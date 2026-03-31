import http from "node:http";
import fs from "node:fs";
import path from "node:path";
import { execFile } from "node:child_process";
import { URL } from "node:url";

// --- CLI / env config ---
function parseArgs() {
  const args = process.argv.slice(2);
  const flags = {};
  for (let i = 0; i < args.length; i++) {
    if (args[i].startsWith("--") && i + 1 < args.length) {
      flags[args[i].slice(2)] = args[++i];
    }
  }
  return {
    id: flags.id || process.env.HOST_AGENT_ID || "default",
    rootPath: flags.path || process.env.HOST_AGENT_PATH || ".",
    port: parseInt(flags.port || process.env.HOST_AGENT_PORT || "9100", 10),
    executables: (flags.executables || process.env.HOST_AGENT_EXECUTABLES || "")
      .split(",").map(s => s.trim()).filter(Boolean),
    key: flags.key || process.env.HOST_AGENT_KEY || "",
  };
}

const config = parseArgs();
config.rootPath = path.resolve(config.rootPath);

// Validate root path
if (!fs.existsSync(config.rootPath) || !fs.statSync(config.rootPath).isDirectory()) {
  console.error(`Error: path "${config.rootPath}" does not exist or is not a directory.`);
  process.exit(1);
}

// --- Helpers ---
function safePath(rel) {
  const resolved = path.resolve(config.rootPath, rel);
  if (!resolved.startsWith(config.rootPath + path.sep) && resolved !== config.rootPath) return null;
  return resolved;
}

function json(res, status, data) {
  res.writeHead(status, {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, Authorization",
  });
  res.end(JSON.stringify(data));
}

function readBody(req) {
  return new Promise((resolve, reject) => {
    const chunks = [];
    req.on("data", c => chunks.push(c));
    req.on("end", () => {
      try { resolve(JSON.parse(Buffer.concat(chunks).toString())); }
      catch { reject(new Error("Invalid JSON body")); }
    });
    req.on("error", reject);
  });
}

function checkAuth(req, res) {
  if (!config.key) return true;
  const header = req.headers["authorization"] || "";
  if (header === `Bearer ${config.key}`) return true;
  json(res, 401, { error: "Unauthorized" });
  return false;
}

// --- Handlers ---
async function handleHealth(_req, res) {
  json(res, 200, { status: "ok", id: config.id, path: config.rootPath });
}

async function handleExec(req, res) {
  const body = await readBody(req);
  const { command, args = [], timeout = 120000 } = body;
  if (!command || !config.executables.includes(command)) {
    return json(res, 403, { error: `Command "${command}" is not in the allowlist` });
  }
  execFile(command, args, { cwd: config.rootPath, timeout, windowsHide: true }, (err, stdout, stderr) => {
    json(res, 200, {
      stdout: stdout || "",
      stderr: stderr || "",
      exit_code: err ? (err.code ?? 1) : 0,
    });
  });
}

async function handleList(req, res) {
  const url = new URL(req.url, `http://${req.headers.host}`);
  const rel = url.searchParams.get("path") || ".";
  const abs = safePath(rel);
  if (!abs) return json(res, 403, { error: "Path traversal denied" });
  try {
    const dirents = fs.readdirSync(abs, { withFileTypes: true });
    const entries = dirents.map(d => {
      const entry = { name: d.name, type: d.isDirectory() ? "directory" : "file" };
      if (!d.isDirectory()) {
        try { entry.size = fs.statSync(path.join(abs, d.name)).size; } catch { entry.size = 0; }
      }
      return entry;
    });
    json(res, 200, { entries });
  } catch (e) {
    json(res, 404, { error: e.message });
  }
}

async function handleRead(req, res) {
  const url = new URL(req.url, `http://${req.headers.host}`);
  const rel = url.searchParams.get("path") || "";
  const abs = safePath(rel);
  if (!abs) return json(res, 403, { error: "Path traversal denied" });
  try {
    const stat = fs.statSync(abs);
    if (stat.size > 1_048_576) return json(res, 413, { error: "File exceeds 1MB limit" });
    const content = fs.readFileSync(abs, "utf-8");
    json(res, 200, { content, size: stat.size });
  } catch (e) {
    json(res, 404, { error: e.message });
  }
}

async function handleWrite(req, res) {
  const body = await readBody(req);
  const { path: rel, content } = body;
  if (!rel || content === undefined) return json(res, 400, { error: "Missing path or content" });
  const abs = safePath(rel);
  if (!abs) return json(res, 403, { error: "Path traversal denied" });
  try {
    fs.mkdirSync(path.dirname(abs), { recursive: true });
    fs.writeFileSync(abs, content, "utf-8");
    json(res, 200, { ok: true, path: rel });
  } catch (e) {
    json(res, 500, { error: e.message });
  }
}

// --- Router ---
const routes = {
  "GET /health": handleHealth,
  "POST /exec": handleExec,
  "GET /list": handleList,
  "GET /read": handleRead,
  "POST /write": handleWrite,
};

const server = http.createServer(async (req, res) => {
  if (req.method === "OPTIONS") return json(res, 204, {});
  if (!checkAuth(req, res)) return;
  const pathname = new URL(req.url, `http://${req.headers.host}`).pathname;
  const handler = routes[`${req.method} ${pathname}`];
  if (!handler) return json(res, 404, { error: "Not found" });
  try { await handler(req, res); } catch (e) { json(res, 500, { error: e.message }); }
});

server.listen(config.port, "0.0.0.0", () => {
  console.log(`\n  Axon Host Agent`);
  console.log(`  ────────────────────────────`);
  console.log(`  ID:          ${config.id}`);
  console.log(`  Path:        ${config.rootPath}`);
  console.log(`  Port:        ${config.port}`);
  console.log(`  Executables: ${config.executables.join(", ") || "(none)"}`);
  console.log(`  Auth:        ${config.key ? "enabled" : "disabled"}`);
  console.log(`  ────────────────────────────\n`);
});
