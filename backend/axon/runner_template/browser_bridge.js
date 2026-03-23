/**
 * Browser bridge — web automation via Playwright.
 * Uses Claude to generate Playwright scripts, then executes them.
 * Requires: npm install playwright (on the host).
 */

const { execSync } = require("child_process");
const fs = require("fs");
const os = require("os");
const path = require("path");
const { runClaude } = require("./claude_util");

function _log(level, msg) {
  const ts = new Date().toTimeString().slice(0, 8);
  console.log(`${ts} [${level}] ${msg}`);
}

function _loadTypeConfig() {
  const configPath = path.join(__dirname, "config.json");
  const config = JSON.parse(fs.readFileSync(configPath, "utf-8"));
  return config.type_config || {};
}

async function generatePlan(workDir, taskDescription) {
  const tc = _loadTypeConfig();
  const startUrl = tc.start_url || "";

  const prompt =
    "You are a web automation specialist using Playwright. " +
    "Create a plan for the following browser automation task. " +
    (startUrl ? `Starting URL: ${startUrl}. ` : "") +
    "Describe the steps: navigate, click, fill, extract data, screenshot, etc. " +
    "Do NOT write code yet — only output the plan.\n\n" +
    `Task: ${taskDescription}`;

  _log("INFO", `Generating browser plan`);
  const { stdout, stderr, exitCode } = await runClaude(workDir, prompt);

  if (exitCode !== 0) {
    throw new Error(`Browser plan failed: ${stderr.trim()}`);
  }

  return stdout.trim();
}

async function executePlan(workDir, plan) {
  // Have Claude generate a Playwright script from the plan
  const prompt =
    "Generate a complete Playwright script (Node.js) for the following plan. " +
    "Use chromium. Output ONLY the script inside a ```javascript block. " +
    "The script should be self-contained and print results to stdout. " +
    "Include error handling and a browser.close() in a finally block.\n\n" +
    `Plan:\n${plan}`;

  _log("INFO", `Generating Playwright script from plan`);
  const { stdout: scriptResponse, exitCode: genCode } = await runClaude(workDir, prompt);

  if (genCode !== 0) {
    return { success: false, output: "", diff: "", error: "Failed to generate script" };
  }

  // Extract the JavaScript code block
  const match = scriptResponse.match(/```javascript\n([\s\S]*?)```/);
  if (!match) {
    return {
      success: true,
      output: scriptResponse.trim(),
      diff: "",
      error: null,
    };
  }

  const script = match[1];
  const tmpScript = path.join(os.tmpdir(), `axon-pw-${Date.now()}.js`);
  fs.writeFileSync(tmpScript, script, "utf-8");

  _log("INFO", `Executing Playwright script (${script.length} chars)`);
  try {
    const output = execSync(`node "${tmpScript}"`, {
      cwd: workDir,
      encoding: "utf-8",
      stdio: ["pipe", "pipe", "pipe"],
      timeout: 300_000,
    });

    return { success: true, output: output.trim(), diff: "", error: null };
  } catch (err) {
    const stderr = err.stderr?.toString().trim() || err.message;
    return { success: false, output: "", diff: "", error: stderr };
  } finally {
    try { fs.unlinkSync(tmpScript); } catch (_) {}
  }
}

module.exports = { generatePlan, executePlan };
