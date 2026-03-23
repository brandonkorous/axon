/**
 * Documents bridge — PDF/DOCX text extraction and LLM summarization.
 * Uses Python subprocess for document parsing, Claude for analysis.
 */

const { execSync } = require("child_process");
const fs = require("fs");
const path = require("path");
const { runClaude } = require("./claude_util");

function _log(level, msg) {
  const ts = new Date().toTimeString().slice(0, 8);
  console.log(`${ts} [${level}] ${msg}`);
}

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

function _extractText(filePath) {
  const ext = path.extname(filePath).toLowerCase();

  if (ext === ".txt" || ext === ".md") {
    return fs.readFileSync(filePath, "utf-8");
  }

  if (ext === ".pdf") {
    try {
      return execSync(
        `python -c "import pdfplumber; pdf=pdfplumber.open(r'${filePath}'); print('\\n'.join(p.extract_text() or '' for p in pdf.pages)); pdf.close()"`,
        { encoding: "utf-8", stdio: ["pipe", "pipe", "pipe"], timeout: 60_000 }
      ).trim();
    } catch (err) {
      _log("WARN", `PDF extraction failed for ${filePath}: ${err.message}`);
      return `[Failed to extract PDF: ${path.basename(filePath)}]`;
    }
  }

  if (ext === ".docx") {
    try {
      return execSync(
        `python -c "from docx import Document; doc=Document(r'${filePath}'); print('\\n'.join(p.text for p in doc.paragraphs))"`,
        { encoding: "utf-8", stdio: ["pipe", "pipe", "pipe"], timeout: 60_000 }
      ).trim();
    } catch (err) {
      _log("WARN", `DOCX extraction failed for ${filePath}: ${err.message}`);
      return `[Failed to extract DOCX: ${path.basename(filePath)}]`;
    }
  }

  return `[Unsupported format: ${ext}]`;
}

async function generatePlan(workDir, taskDescription) {
  const docs = _listDocuments(workDir);
  const docList = docs.length > 0
    ? `\n\nAvailable documents:\n${docs.map((d) => `- ${path.basename(d)}`).join("\n")}`
    : "\n\nNo documents found in the working directory.";

  const prompt =
    "You are a document analyst. Create a plan for the following task. " +
    "Specify which documents to process and what analysis to perform. " +
    "Do NOT execute — only output the plan.\n\n" +
    `Task: ${taskDescription}${docList}`;

  _log("INFO", `Generating document plan (${docs.length} docs available)`);
  const { stdout, stderr, exitCode } = await runClaude(workDir, prompt);

  if (exitCode !== 0) {
    throw new Error(`Document plan failed: ${stderr.trim()}`);
  }

  return stdout.trim();
}

async function executePlan(workDir, plan) {
  // Extract text from all referenced documents
  const docs = _listDocuments(workDir);
  const extractions = [];

  for (const doc of docs) {
    const basename = path.basename(doc);
    if (plan.toLowerCase().includes(basename.toLowerCase())) {
      _log("INFO", `Extracting text from: ${basename}`);
      const text = _extractText(doc);
      extractions.push(`=== ${basename} ===\n${text}`);
    }
  }

  if (extractions.length === 0) {
    // Process all documents if none specifically referenced
    for (const doc of docs) {
      _log("INFO", `Extracting text from: ${path.basename(doc)}`);
      extractions.push(`=== ${path.basename(doc)} ===\n${_extractText(doc)}`);
    }
  }

  const context = extractions.join("\n\n");
  const prompt =
    `Execute the following plan using the extracted document content.\n\n` +
    `Plan:\n${plan}\n\n` +
    `Document content:\n${context}`;

  _log("INFO", `Executing document plan (${extractions.length} docs, ${context.length} chars)`);
  const { stdout, stderr, exitCode } = await runClaude(workDir, prompt);

  return {
    success: exitCode === 0,
    output: stdout.trim(),
    diff: "",
    error: exitCode !== 0 ? stderr.trim() : null,
  };
}

module.exports = { generatePlan, executePlan };
