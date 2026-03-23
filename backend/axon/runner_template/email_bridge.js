/**
 * Email bridge — read/send emails via Gmail, O365, or Resend.
 * Uses Node.js built-in fetch for HTTP API calls, Claude for composing.
 * Credentials come from config.json type_config section.
 */

const fs = require("fs");
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

// ── Provider: Resend ─────────────────────────────────────────────

async function _resendSend(apiKey, { to, subject, html, from }) {
  const resp = await fetch("https://api.resend.com/emails", {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${apiKey}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ from, to: Array.isArray(to) ? to : [to], subject, html }),
  });
  if (!resp.ok) {
    const err = await resp.text();
    throw new Error(`Resend API error (${resp.status}): ${err}`);
  }
  return resp.json();
}

// ── Provider: Gmail ──────────────────────────────────────────────

async function _gmailList(accessToken, query = "", maxResults = 10) {
  const params = new URLSearchParams({ maxResults: String(maxResults) });
  if (query) params.set("q", query);
  const resp = await fetch(
    `https://gmail.googleapis.com/gmail/v1/users/me/messages?${params}`,
    { headers: { Authorization: `Bearer ${accessToken}` } }
  );
  if (!resp.ok) throw new Error(`Gmail list error (${resp.status})`);
  return resp.json();
}

async function _gmailGet(accessToken, messageId) {
  const resp = await fetch(
    `https://gmail.googleapis.com/gmail/v1/users/me/messages/${messageId}?format=full`,
    { headers: { Authorization: `Bearer ${accessToken}` } }
  );
  if (!resp.ok) throw new Error(`Gmail get error (${resp.status})`);
  return resp.json();
}

// ── Provider: Microsoft Graph (O365) ─────────────────────────────

async function _o365List(accessToken, query = "", top = 10) {
  let url = `https://graph.microsoft.com/v1.0/me/messages?$top=${top}&$orderby=receivedDateTime desc`;
  if (query) url += `&$search="${query}"`;
  const resp = await fetch(url, {
    headers: { Authorization: `Bearer ${accessToken}` },
  });
  if (!resp.ok) throw new Error(`O365 list error (${resp.status})`);
  return resp.json();
}

// ── Bridge interface ─────────────────────────────────────────────

async function generatePlan(workDir, taskDescription) {
  const tc = _loadTypeConfig();
  const provider = tc.email_provider || "unknown";

  const prompt =
    "You are an email assistant. Create a plan for the following email task. " +
    `Email provider: ${provider}. ` +
    "Specify the actions: read, search, compose, or send. " +
    "Do NOT execute — only output the plan.\n\n" +
    `Task: ${taskDescription}`;

  _log("INFO", `Generating email plan (provider: ${provider})`);
  const { stdout, stderr, exitCode } = await runClaude(workDir, prompt);

  if (exitCode !== 0) {
    throw new Error(`Email plan failed: ${stderr.trim()}`);
  }

  return stdout.trim();
}

async function executePlan(workDir, plan) {
  const tc = _loadTypeConfig();
  const provider = tc.email_provider;
  const results = [];

  // Use Claude to interpret the plan and generate structured actions
  const prompt =
    "You are executing an email plan. Analyze the plan and output a JSON array of actions.\n" +
    'Each action: { "action": "send"|"read"|"search", "params": {...} }\n' +
    'For send: params = { "to": "...", "subject": "...", "body": "..." }\n' +
    'For search: params = { "query": "..." }\n' +
    `Plan:\n${plan}`;

  const { stdout, exitCode } = await runClaude(workDir, prompt);

  if (exitCode !== 0) {
    return { success: false, output: "", diff: "", error: "Failed to parse email plan" };
  }

  // Try to extract JSON actions from Claude's response
  let actions = [];
  try {
    const jsonMatch = stdout.match(/\[[\s\S]*\]/);
    if (jsonMatch) actions = JSON.parse(jsonMatch[0]);
  } catch (_) {
    _log("WARN", "Could not parse structured actions, returning plan analysis");
    return { success: true, output: stdout.trim(), diff: "", error: null };
  }

  for (const { action, params } of actions) {
    try {
      if (action === "send" && provider === "resend") {
        const res = await _resendSend(tc.api_key, {
          from: tc.from_address || "noreply@example.com",
          to: params.to,
          subject: params.subject,
          html: params.body,
        });
        results.push(`Sent to ${params.to}: ${JSON.stringify(res)}`);
      } else if (action === "search" && provider === "gmail") {
        const res = await _gmailList(tc.access_token, params.query);
        results.push(`Gmail search "${params.query}": ${(res.messages || []).length} results`);
      } else if (action === "search" && provider === "o365") {
        const res = await _o365List(tc.access_token, params.query);
        results.push(`O365 search "${params.query}": ${(res.value || []).length} results`);
      } else {
        results.push(`Unsupported action: ${action} for provider ${provider}`);
      }
    } catch (err) {
      results.push(`Error (${action}): ${err.message}`);
    }
  }

  const output = results.join("\n");
  return { success: true, output, diff: "", error: null };
}

module.exports = { generatePlan, executePlan };
