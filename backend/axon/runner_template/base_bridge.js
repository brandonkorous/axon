/**
 * Base Bridge — standardized worker bridge factory.
 *
 * Usage:
 *   const { createBridge } = require("./base_bridge");
 *   module.exports = createBridge({
 *     name: "my-bridge",
 *     description: "Does something useful",
 *     capabilities: ["read", "write"],
 *     requiredConfig: [],
 *     generatePlan: async (ctx, taskDescription) => "...",
 *     executePlan: async (ctx, plan) => ({ success: true, output: "..." }),
 *   });
 */

const fs = require("fs");
const path = require("path");

const RUNNER_DIR = __dirname;

function _timestamp() {
  return new Date().toTimeString().slice(0, 8);
}

function _loadTypeConfig() {
  try {
    const cfg = JSON.parse(
      fs.readFileSync(path.join(RUNNER_DIR, "config.json"), "utf-8"),
    );
    return cfg.type_config || {};
  } catch (_) {
    return {};
  }
}

function _buildCtx(workDir, bridgeName) {
  return {
    workDir,
    log(level, msg) {
      console.log(`${_timestamp()} [${level}] [bridge:${bridgeName}] ${msg}`);
    },
    loadTypeConfig: _loadTypeConfig,
  };
}

function _normalizeResult(raw) {
  if (!raw || typeof raw !== "object") {
    return { success: false, output: String(raw ?? ""), diff: "", error: "Bridge returned non-object result" };
  }
  return {
    success: Boolean(raw.success),
    output: String(raw.output ?? ""),
    diff: String(raw.diff ?? ""),
    error: raw.error != null ? String(raw.error) : null,
  };
}

/**
 * Create a validated, wrapped bridge module from a spec.
 *
 * @param {object} spec
 * @param {string} spec.name
 * @param {string} spec.description
 * @param {string[]} spec.capabilities
 * @param {string[]} [spec.requiredConfig]
 * @param {(ctx, taskDescription: string) => Promise<string>} spec.generatePlan
 * @param {(ctx, plan: string) => Promise<object>} spec.executePlan
 * @returns {{ meta, generatePlan, executePlan }}
 */
function createBridge(spec) {
  if (!spec.name) throw new Error("Bridge spec missing 'name'");
  if (typeof spec.generatePlan !== "function") throw new Error(`Bridge ${spec.name}: missing generatePlan()`);
  if (typeof spec.executePlan !== "function") throw new Error(`Bridge ${spec.name}: missing executePlan()`);

  const meta = {
    name: spec.name,
    description: spec.description || "",
    capabilities: spec.capabilities || [],
    requiredConfig: spec.requiredConfig || [],
  };

  async function generatePlan(workDir, taskDescription) {
    const ctx = _buildCtx(workDir, spec.name);
    try {
      const plan = await spec.generatePlan(ctx, taskDescription);
      return String(plan);
    } catch (err) {
      ctx.log("ERROR", `generatePlan failed: ${err.message}`);
      throw err;
    }
  }

  async function executePlan(workDir, plan) {
    const ctx = _buildCtx(workDir, spec.name);
    try {
      const raw = await spec.executePlan(ctx, plan);
      return _normalizeResult(raw);
    } catch (err) {
      ctx.log("ERROR", `executePlan failed: ${err.message}`);
      return { success: false, output: "", diff: "", error: err.message };
    }
  }

  return { meta, generatePlan, executePlan };
}

module.exports = { createBridge };
