"""Shell access plugin — host filesystem and executable access for agents."""

from axon.plugins.builtin.shell_access.plugin import ShellAccessPlugin
from axon.plugins.registry import register_plugin

register_plugin("shell_access", ShellAccessPlugin)
