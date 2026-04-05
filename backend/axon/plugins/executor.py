"""PluginToolExecutor — instance-aware routing of tool calls to plugins."""

from __future__ import annotations

import copy
import json
from typing import Any

from axon.logging import get_logger
from axon.plugins.base import BasePlugin

logger = get_logger(__name__)


class PluginToolExecutor:
    """Routes tool calls to the correct plugin instance.

    Supports multiple instances of the same plugin per agent. When an agent
    has more than one instance of a plugin, an ``instance`` parameter is
    injected into each tool schema so the LLM can specify which one to use.
    """

    def __init__(
        self,
        instance_map: dict[str, list[tuple[str, BasePlugin]]],
    ) -> None:
        """
        Args:
            instance_map: ``{plugin_name: [(instance_id, plugin), ...]}``
        """
        self._instance_map = instance_map
        # tool_name → plugin_name (for routing)
        self._tool_to_plugin: dict[str, str] = {}
        self._tools: list[dict[str, Any]] = []
        self._build_tools()

    def _build_tools(self) -> None:
        """Collect tool schemas from all plugins, injecting instance param when needed."""
        for plugin_name, instances in self._instance_map.items():
            if not instances:
                continue
            # Get base schemas from the first instance (all share the same schema)
            base_schemas = instances[0][1].get_tools()
            multi = len(instances) > 1

            for schema in base_schemas:
                tool = copy.deepcopy(schema)
                func = tool.get("function", {})
                name = func.get("name", "")
                if name:
                    self._tool_to_plugin[name] = plugin_name

                if multi:
                    # Inject instance parameter and descriptive labels
                    ids = [iid for iid, _ in instances]
                    label_parts = []
                    for iid, p in instances:
                        img = getattr(p, "_image", "")
                        desc = f"{iid}"
                        if img:
                            desc += f" [{img}]"
                        label_parts.append(desc)
                    labels = ", ".join(label_parts)
                    func["description"] = (
                        func.get("description", "")
                        + f"\nAvailable instances: {labels}."
                    )
                    params = func.setdefault("parameters", {})
                    props = params.setdefault("properties", {})
                    props["instance"] = {
                        "type": "string",
                        "enum": ids,
                        "description": "Which instance to use",
                    }
                    required = params.setdefault("required", [])
                    if "instance" not in required:
                        required.insert(0, "instance")

                self._tools.append(tool)

    @property
    def tools(self) -> list[dict[str, Any]]:
        return list(self._tools)

    @property
    def tool_names(self) -> set[str]:
        return set(self._tool_to_plugin.keys())

    def can_handle(self, tool_name: str) -> bool:
        return tool_name in self._tool_to_plugin

    async def execute(self, tool_name: str, arguments: str) -> str:
        """Execute a tool call, resolving the correct plugin instance."""
        plugin_name = self._tool_to_plugin.get(tool_name)
        if not plugin_name:
            return json.dumps({"error": f"No plugin handles tool: {tool_name}"})

        instances = self._instance_map.get(plugin_name, [])
        if not instances:
            return json.dumps({"error": f"No instances for plugin: {plugin_name}"})

        try:
            args: dict[str, Any] = json.loads(arguments) if arguments else {}
        except json.JSONDecodeError:
            args = {}

        # Resolve instance
        instance_id = args.pop("instance", None)
        remaining = json.dumps(args)

        if len(instances) == 1:
            _, plugin = instances[0]
        elif instance_id:
            plugin = next(
                (p for iid, p in instances if iid == instance_id), None,
            )
            if not plugin:
                valid = [iid for iid, _ in instances]
                return json.dumps({
                    "error": f"Unknown instance '{instance_id}'. Valid: {valid}",
                })
        else:
            valid = [iid for iid, _ in instances]
            return json.dumps({
                "error": f"Multiple instances available — specify 'instance': {valid}",
            })

        try:
            return await plugin.execute(tool_name, remaining)
        except Exception as e:
            logger.exception("Plugin %s failed on tool %s", plugin_name, tool_name)
            return json.dumps({"error": f"Plugin error: {e}"})
