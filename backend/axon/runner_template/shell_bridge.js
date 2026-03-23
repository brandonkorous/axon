/**
 * Shell bridge — direct command execution without LLM.
 * Parses task descriptions as command lists and executes them sequentially.
 * Zero external dependencies — Node.js built-ins only.
 */

const { execSync } = require("child_process");

function _log(level, msg) {
  const ts = new Date().toTimeString().slice(0, 8);
  console.log(`${ts} [${level}] ${msg}`);
}

/**
 * Parse a task description into executable commands.
 * Supports JSON array format or newline-separated commands.
 */
function _parseCommands(text) {
  const trimmed = text.trim();

  // Try JSON array first: ["cmd1", "cmd2"]
  if (trimmed.startsWith("[")) {
    try {
      const parsed = JSON.parse(trimmed);
      if (Array.isArray(parsed)) return parsed.map(String);
    } catch (_) {}
  }

  // Fall back to newline-separated (skip empty lines and comments)
  return trimmed
    .split(/\r?\n/)
    .map((l) => l.trim())
    .filter((l) => l && !l.startsWith("#"));
}

async function generatePlan(workDir, taskDescription) {
  const commands = _parseCommands(taskDescription);
  _log("INFO", `Shell plan: ${commands.length} command(s) to execute`);

  const plan = commands
    .map((cmd, i) => `${i + 1}. ${cmd}`)
    .join("\n");

  return `Shell execution plan:\n${plan}`;
}

async function executePlan(workDir, plan) {
  // Extract commands from the numbered plan format
  const commands = plan
    .split(/\r?\n/)
    .map((l) => l.replace(/^\d+\.\s*/, "").trim())
    .filter((l) => l && !l.startsWith("Shell execution plan"));

  if (commands.length === 0) {
    return { success: false, output: "", diff: "", error: "No commands to execute" };
  }

  const outputs = [];
  for (const cmd of commands) {
    _log("INFO", `Executing: ${cmd}`);
    try {
      const output = execSync(cmd, {
        cwd: workDir,
        encoding: "utf-8",
        stdio: ["pipe", "pipe", "pipe"],
        timeout: 120_000,
      });
      outputs.push(`$ ${cmd}\n${output.trim()}`);
    } catch (err) {
      const stderr = err.stderr?.toString().trim() || err.message;
      outputs.push(`$ ${cmd}\nERROR: ${stderr}`);
      _log("ERROR", `Command failed: ${cmd} — ${stderr}`);
      return {
        success: false,
        output: outputs.join("\n\n"),
        diff: "",
        error: `Command failed: ${cmd}\n${stderr}`,
      };
    }
  }

  return {
    success: true,
    output: outputs.join("\n\n"),
    diff: "",
    error: null,
  };
}

module.exports = { generatePlan, executePlan };
