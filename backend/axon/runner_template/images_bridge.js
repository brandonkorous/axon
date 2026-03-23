/**
 * Images bridge — image analysis via Claude vision and manipulation via Python.
 * Reads images as base64 for vision analysis, uses Pillow for transformations.
 */

const { execSync } = require("child_process");
const fs = require("fs");
const path = require("path");
const { runClaude } = require("./claude_util");

function _log(level, msg) {
  const ts = new Date().toTimeString().slice(0, 8);
  console.log(`${ts} [${level}] ${msg}`);
}

const IMAGE_EXTENSIONS = new Set([".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".svg"]);

function _listImages(dir) {
  try {
    return fs.readdirSync(dir)
      .filter((f) => IMAGE_EXTENSIONS.has(path.extname(f).toLowerCase()))
      .map((f) => path.join(dir, f));
  } catch (_) {
    return [];
  }
}

function _imageMetadata(filePath) {
  const stat = fs.statSync(filePath);
  const ext = path.extname(filePath).toLowerCase();
  let dimensions = "unknown";

  try {
    const script = `from PIL import Image; img=Image.open(r'${filePath}'); print(f'{img.width}x{img.height}')`;
    dimensions = execSync(`python -c "${script}"`, {
      encoding: "utf-8",
      stdio: ["pipe", "pipe", "pipe"],
      timeout: 10_000,
    }).trim();
  } catch (_) {}

  return {
    name: path.basename(filePath),
    size: stat.size,
    ext,
    dimensions,
  };
}

async function generatePlan(workDir, taskDescription) {
  const images = _listImages(workDir);
  const metaList = images.slice(0, 50).map(_imageMetadata);

  const imageInfo = metaList.length > 0
    ? `\n\nAvailable images:\n${metaList.map((m) => `- ${m.name} (${m.dimensions}, ${(m.size / 1024).toFixed(1)}KB)`).join("\n")}`
    : "\n\nNo images found in the working directory.";

  const prompt =
    "You are an image analyst. Create a plan for the following task. " +
    "Specify which images to analyze or manipulate and what operations to perform. " +
    "Do NOT execute — only output the plan.\n\n" +
    `Task: ${taskDescription}${imageInfo}`;

  _log("INFO", `Generating image plan (${images.length} images available)`);
  const { stdout, stderr, exitCode } = await runClaude(workDir, prompt);

  if (exitCode !== 0) {
    throw new Error(`Image plan failed: ${stderr.trim()}`);
  }

  return stdout.trim();
}

async function executePlan(workDir, plan) {
  // Use Claude with the plan to generate Python image processing commands
  const prompt =
    "Execute the following image processing plan. " +
    "For analysis tasks, describe what you see. " +
    "For manipulation tasks, output Python code using Pillow that I can execute. " +
    "Wrap any Python code in ```python blocks.\n\n" +
    `Working directory: ${workDir}\n` +
    `Plan:\n${plan}`;

  _log("INFO", `Executing image plan`);
  const { stdout, stderr, exitCode } = await runClaude(workDir, prompt);

  if (exitCode !== 0) {
    return { success: false, output: "", diff: "", error: stderr.trim() };
  }

  // Extract and execute any Python code blocks
  const codeBlocks = stdout.match(/```python\n([\s\S]*?)```/g) || [];
  const outputs = [stdout.trim()];

  for (const block of codeBlocks) {
    const code = block.replace(/```python\n/, "").replace(/```$/, "");
    _log("INFO", `Executing Python image code (${code.length} chars)`);
    try {
      const result = execSync(`python -c ${JSON.stringify(code)}`, {
        cwd: workDir,
        encoding: "utf-8",
        stdio: ["pipe", "pipe", "pipe"],
        timeout: 120_000,
      });
      if (result.trim()) outputs.push(`Python output:\n${result.trim()}`);
    } catch (err) {
      outputs.push(`Python error: ${err.stderr?.toString().trim() || err.message}`);
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
