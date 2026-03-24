/**
 * Documents bridge — PDF/DOCX parsing, analysis, and generation.
 * Built on the base bridge standard.
 */

const { execSync } = require("child_process");
const fs = require("fs");
const path = require("path");
const { createBridge } = require("./base_bridge");
const { runClaude } = require("./claude_util");
const { render } = require("./doc_renderers");

const DOC_EXTENSIONS = new Set([".pdf", ".docx", ".doc", ".txt", ".md", ".rtf"]);

function _listDocuments(dir) {
  try {
    return fs.readdirSync(dir)
      .filter((f) => DOC_EXTENSIONS.has(path.extname(f).toLowerCase()))
      .map((f) => path.join(dir, f));
  } catch (_) {
    return [];
  }
}

function _extractText(filePath, log) {
  const ext = path.extname(filePath).toLowerCase();

  if (ext === ".txt" || ext === ".md") {
    return fs.readFileSync(filePath, "utf-8");
  }

  if (ext === ".pdf") {
    try {
      return execSync(
        `python -c "import pdfplumber; pdf=pdfplumber.open(r'${filePath}'); print('\\n'.join(p.extract_text() or '' for p in pdf.pages)); pdf.close()"`,
        { encoding: "utf-8", stdio: ["pipe", "pipe", "pipe"], timeout: 60_000 },
      ).trim();
    } catch (err) {
      log("WARN", `PDF extraction failed for ${filePath}: ${err.message}`);
      return `[Failed to extract PDF: ${path.basename(filePath)}]`;
    }
  }

  if (ext === ".docx") {
    try {
      return execSync(
        `python -c "from docx import Document; doc=Document(r'${filePath}'); print('\\n'.join(p.text for p in doc.paragraphs))"`,
        { encoding: "utf-8", stdio: ["pipe", "pipe", "pipe"], timeout: 60_000 },
      ).trim();
    } catch (err) {
      log("WARN", `DOCX extraction failed for ${filePath}: ${err.message}`);
      return `[Failed to extract DOCX: ${path.basename(filePath)}]`;
    }
  }

  return `[Unsupported format: ${ext}]`;
}

// ── Parse mode: extract + analyze ────────────────────────────────

async function _executeParse(ctx, plan) {
  const docs = _listDocuments(ctx.workDir);
  const extractions = [];

  for (const doc of docs) {
    const basename = path.basename(doc);
    if (plan.toLowerCase().includes(basename.toLowerCase())) {
      ctx.log("INFO", `Extracting: ${basename}`);
      extractions.push(`=== ${basename} ===\n${_extractText(doc, ctx.log)}`);
    }
  }

  if (extractions.length === 0) {
    for (const doc of docs) {
      ctx.log("INFO", `Extracting: ${path.basename(doc)}`);
      extractions.push(`=== ${path.basename(doc)} ===\n${_extractText(doc, ctx.log)}`);
    }
  }

  const context = extractions.join("\n\n");
  const prompt = `Execute the following plan using the extracted document content.\n\nPlan:\n${plan}\n\nDocument content:\n${context}`;

  ctx.log("INFO", `Analyzing ${extractions.length} docs (${context.length} chars)`);
  const { stdout, stderr, exitCode } = await runClaude(ctx.workDir, prompt);

  return { success: exitCode === 0, output: stdout.trim(), diff: "", error: exitCode !== 0 ? stderr.trim() : null };
}

// ── Generate mode: create new documents ──────────────────────────

async function _executeGenerate(ctx, plan) {
  const prompt =
    "You are a document generator. Based on the plan below, produce a JSON object with this exact structure:\n" +
    '{ "format": "pdf"|"docx"|"html", "filename": "my-document", "content": { "title": "...", "sections": [{ "heading": "...", "body": "..." }] } }\n\n' +
    "Output ONLY the JSON, no markdown fences or explanation.\n\n" +
    `Plan:\n${plan}`;

  ctx.log("INFO", "Generating document structure via Claude");
  const { stdout, stderr, exitCode } = await runClaude(ctx.workDir, prompt);

  if (exitCode !== 0) {
    return { success: false, output: "", diff: "", error: `Claude failed: ${stderr.trim()}` };
  }

  let spec;
  try {
    const cleaned = stdout.trim().replace(/^```json?\s*/i, "").replace(/```\s*$/, "");
    spec = JSON.parse(cleaned);
  } catch (err) {
    return { success: false, output: stdout.trim(), diff: "", error: `Failed to parse document spec: ${err.message}` };
  }

  const config = ctx.loadTypeConfig();
  const outputDir = config.output_dir || ctx.workDir;
  if (!fs.existsSync(outputDir)) fs.mkdirSync(outputDir, { recursive: true });

  const ext = { pdf: ".pdf", docx: ".docx", html: ".html" }[spec.format] || ".html";
  const outputPath = path.join(outputDir, `${spec.filename || "document"}${ext}`);

  ctx.log("INFO", `Rendering ${spec.format} → ${outputPath}`);
  const actualPath = await render(outputPath, spec.format, spec.content, ctx.log);

  return { success: true, output: `Document created: ${actualPath}`, diff: "", error: null };
}

// ── Bridge definition ────────────────────────────────────────────

module.exports = createBridge({
  name: "documents",
  description: "PDF/DOCX parsing, analysis, and generation",
  capabilities: ["parse", "generate"],
  requiredConfig: [],

  async generatePlan(ctx, taskDescription) {
    const docs = _listDocuments(ctx.workDir);
    const docList = docs.length > 0
      ? `\n\nAvailable documents:\n${docs.map((d) => `- ${path.basename(d)}`).join("\n")}`
      : "\n\nNo documents found in the working directory.";

    const prompt =
      "You are a document specialist. Create a plan for the following task.\n" +
      "First, determine the mode:\n" +
      "- If the task involves analyzing existing documents, start your plan with [MODE: parse]\n" +
      "- If the task involves creating/writing a new document, start your plan with [MODE: generate]\n" +
      "Then describe the steps. Do NOT execute — only output the plan.\n\n" +
      `Task: ${taskDescription}${docList}`;

    ctx.log("INFO", `Generating plan (${docs.length} docs available)`);
    const { stdout, stderr, exitCode } = await runClaude(ctx.workDir, prompt);

    if (exitCode !== 0) throw new Error(`Plan generation failed: ${stderr.trim()}`);
    return stdout.trim();
  },

  async executePlan(ctx, plan) {
    const isGenerate = /\[MODE:\s*generate\]/i.test(plan);
    ctx.log("INFO", `Mode: ${isGenerate ? "generate" : "parse"}`);

    if (isGenerate) return _executeGenerate(ctx, plan);
    return _executeParse(ctx, plan);
  },
});
