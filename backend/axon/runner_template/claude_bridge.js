/**
 * Backward-compatibility shim — delegates to code_bridge.js.
 * Existing runners that require("./claude_bridge") will still work.
 */
module.exports = require("./code_bridge");
