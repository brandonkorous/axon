"""Sandbox plugin — containerized execution environment for agents."""

from axon.plugins.builtin.sandbox.plugin import SandboxPlugin
from axon.plugins.registry import register_plugin

register_plugin("sandbox", SandboxPlugin)
