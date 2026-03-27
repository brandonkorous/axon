/**
 * Shared Claude Code CLI helpers — used by bridges that need LLM capabilities.
 * Zero external dependencies — Node.js built-ins only.
 */

const { execSync, spawn } = require("child_process");
const fs = require("fs");
const os = require("os");
const path = require("path");

function _log(level, msg) {
  const ts = new Date().toTimeString().slice(0, 8);
  console.log(`${ts} [${level}] ${msg}`);
}

function claudeCmd() {
  // Try system PATH first
  try {
    const cmd = os.platform() === "win32" ? "where claude" : "which claude";
    const result = execSync(cmd, { encoding: "utf-8", stdio: ["pipe", "pipe", "pipe"] }).trim();
    const first = result.split(/\r?\n/)[0];
    if (first) {
      _log("DEBUG", `Claude CLI found via PATH: ${first}`);
      return first;
    }
  } catch (_) {
    _log("DEBUG", `Claude not on PATH (platform=${os.platform()})`);
  }

  // Fallback paths
  if (os.platform() === "win32") {
    const appdata = process.env.APPDATA || "";
    const npmGlobal = path.join(appdata, "npm", "claude.cmd");
    _log("DEBUG", `Checking fallback: ${npmGlobal} (APPDATA=${appdata})`);
    if (fs.existsSync(npmGlobal)) return npmGlobal;
  } else {
    const unixFallback = "/usr/local/bin/claude";
    if (fs.existsSync(unixFallback)) return unixFallback;
  }

  _log("DEBUG", `PATH=${process.env.PATH}`);
  throw new Error(
    "Claude CLI not found. Install it with: npm install -g @anthropic-ai/claude-code"
  );
}

function runClaude(workDir, prompt, extraArgs = []) {
  return new Promise((resolve, reject) => {
    const tmpFile = path.join(os.tmpdir(), `axon-prompt-${Date.now()}.txt`);
    fs.writeFileSync(tmpFile, prompt, "utf-8");

    const args = ["--print", ...extraArgs];
    const stdin = fs.openSync(tmpFile, "r");

    // Ensure Node.js directory is on PATH for claude.cmd to find node
    const env = { ...process.env };
    const nodeDir = path.dirname(process.execPath);
    if (env.PATH && !env.PATH.includes(nodeDir)) {
      env.PATH = nodeDir + path.delimiter + env.PATH;
    }

    const proc = spawn(claudeCmd(), args, {
      cwd: workDir,
      stdio: [stdin, "pipe", "pipe"],
      shell: os.platform() === "win32",
      env,
    });

    const stdoutChunks = [];
    const stderrChunks = [];

    proc.stdout.on("data", (d) => {
      stdoutChunks.push(d);
      // Stream to console (appears in runner.log) for real-time visibility
      process.stdout.write(d);
    });
    proc.stderr.on("data", (d) => {
      stderrChunks.push(d);
      process.stderr.write(d);
    });

    proc.on("error", (err) => {
      fs.closeSync(stdin);
      try { fs.unlinkSync(tmpFile); } catch (_) {}
      reject(err);
    });

    proc.on("close", (exitCode) => {
      fs.closeSync(stdin);
      try { fs.unlinkSync(tmpFile); } catch (_) {}
      resolve({
        stdout: Buffer.concat(stdoutChunks).toString("utf-8"),
        stderr: Buffer.concat(stderrChunks).toString("utf-8"),
        exitCode,
      });
    });
  });
}

module.exports = { claudeCmd, runClaude };
