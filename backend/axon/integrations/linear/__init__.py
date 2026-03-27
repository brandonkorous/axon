"""Linear integration — register on import."""

from axon.integrations.linear.integration import LinearIntegration
from axon.integrations.registry import register_integration

register_integration("linear", LinearIntegration)
