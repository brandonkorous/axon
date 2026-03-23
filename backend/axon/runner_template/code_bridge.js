/**
 * Code bridge — plan generation and execution via Claude Code CLI.
 * Uses shared claude_util for CLI invocation.
 */

const { execSync } = require("child_process");
const { runClaude } = require("./claude_util");

function _log(level, msg) {
  const ts = new Date().toTimeString().slice(0, 8);
  console.log(`${ts} [${level}] ${msg}`);
}

async function generatePlan(workDir, taskDescription) {
  const prompt =
    "You are acting as an Enterprise Architect. " +
    "Create a detailed implementation plan for the following task. " +
    "Do NOT execute any changes — only output the plan.\n\n" +
    `Task: ${taskDescription}`;

  _log("INFO", `Generating plan for: ${taskDescription.slice(0, 80)}`);
  const { stdout, stderr, exitCode } = await runClaude(workDir, prompt);

  if (exitCode !== 0) {
    const error = stderr.trim();
    _log("ERROR", `Claude Code plan failed: ${error}`);
    throw new Error(`Claude Code plan failed: ${error}`);
  }

  const plan = stdout.trim();
  _log("INFO", `Plan generated (${plan.length} chars)`);
  return plan;
}

async function executePlan(workDir, plan) {
  const prompt =
    "Execute the following approved implementation plan exactly as specified. " +
    "Make all the code changes described.\n\n" +
    `Plan:\n${plan}`;

  _log("INFO", `Executing approved plan (${plan.length} chars)`);
  const { stdout, stderr, exitCode } = await runClaude(
    workDir, prompt, ["--dangerously-skip-permissions"]
  );

  // Capture git diff for the result
  let diff = "";
  try {
    diff = execSync("git diff --stat", {
      cwd: workDir,
      encoding: "utf-8",
      stdio: ["pipe", "pipe", "pipe"],
    }).trim();
  } catch (_) {}

  return {
    success: exitCode === 0,
    output: stdout.trim(),
    diff,
    error: exitCode !== 0 ? stderr.trim() : null,
  };
}

module.exports = { generatePlan, executePlan };
