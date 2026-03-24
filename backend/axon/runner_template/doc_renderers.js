/**
 * Document renderers — PDF, DOCX, and HTML output.
 * PDF and DOCX require npm dependencies (pdfkit, docx).
 * HTML is always available as a zero-dependency fallback.
 */

const fs = require("fs");
const path = require("path");

/**
 * Render a document to the given format.
 * Falls back to HTML if the requested format's dependency is missing.
 *
 * @param {string} outputPath - Full path for the output file
 * @param {"pdf"|"docx"|"html"} format
 * @param {{ title: string, sections: Array<{ heading: string, body: string }> }} content
 * @param {function} log - Scoped logger from bridge ctx
 * @returns {string} Actual output path (may differ if fallback used)
 */
async function render(outputPath, format, content, log) {
  const renderers = { pdf: _renderPdf, docx: _renderDocx, html: _renderHtml };
  const fn = renderers[format];
  if (!fn) {
    log("WARN", `Unknown format "${format}", falling back to HTML`);
    return _renderHtml(_swapExt(outputPath, ".html"), content, log);
  }
  try {
    return await fn(outputPath, content, log);
  } catch (err) {
    if (err.code === "MODULE_NOT_FOUND") {
      log("WARN", `${format} dependency missing — falling back to HTML. Run npm install in the runner directory.`);
      return _renderHtml(_swapExt(outputPath, ".html"), content, log);
    }
    throw err;
  }
}

function _swapExt(filePath, ext) {
  const dir = path.dirname(filePath);
  const base = path.basename(filePath, path.extname(filePath));
  return path.join(dir, base + ext);
}

async function _renderPdf(outputPath, content, log) {
  const PDFDocument = require("pdfkit");
  return new Promise((resolve, reject) => {
    const doc = new PDFDocument({ margin: 50 });
    const stream = fs.createWriteStream(outputPath);
    doc.pipe(stream);

    doc.fontSize(22).font("Helvetica-Bold").text(content.title, { align: "center" });
    doc.moveDown(1.5);

    for (const section of content.sections || []) {
      if (section.heading) {
        doc.fontSize(14).font("Helvetica-Bold").text(section.heading);
        doc.moveDown(0.3);
      }
      if (section.body) {
        doc.fontSize(11).font("Helvetica").text(section.body, { lineGap: 2 });
        doc.moveDown(1);
      }
    }

    doc.end();
    stream.on("finish", () => { log("INFO", `PDF written: ${outputPath}`); resolve(outputPath); });
    stream.on("error", reject);
  });
}

async function _renderDocx(outputPath, content, log) {
  const { Document, Packer, Paragraph, TextRun, HeadingLevel } = require("docx");

  const children = [
    new Paragraph({ text: content.title, heading: HeadingLevel.TITLE }),
  ];

  for (const section of content.sections || []) {
    if (section.heading) {
      children.push(new Paragraph({ text: section.heading, heading: HeadingLevel.HEADING_1 }));
    }
    if (section.body) {
      for (const line of section.body.split("\n")) {
        children.push(new Paragraph({ children: [new TextRun(line)] }));
      }
    }
  }

  const doc = new Document({ sections: [{ children }] });
  const buffer = await Packer.toBuffer(doc);
  fs.writeFileSync(outputPath, buffer);
  log("INFO", `DOCX written: ${outputPath}`);
  return outputPath;
}

async function _renderHtml(outputPath, content, log) {
  const sections = (content.sections || [])
    .map((s) => {
      const h = s.heading ? `<h2>${_esc(s.heading)}</h2>` : "";
      const b = s.body ? `<p>${_esc(s.body).replace(/\n/g, "<br>")}</p>` : "";
      return `<section>${h}${b}</section>`;
    })
    .join("\n");

  const html = `<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><title>${_esc(content.title)}</title>
<style>body{font-family:system-ui,sans-serif;max-width:800px;margin:2rem auto;padding:0 1rem;line-height:1.6}
h1{border-bottom:2px solid #333;padding-bottom:.5rem}h2{margin-top:1.5rem;color:#444}
section{margin-bottom:1rem}</style></head>
<body><h1>${_esc(content.title)}</h1>${sections}</body></html>`;

  fs.writeFileSync(outputPath, html, "utf-8");
  log("INFO", `HTML written: ${outputPath}`);
  return outputPath;
}

function _esc(str) {
  return String(str).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

module.exports = { render };
