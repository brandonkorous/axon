"""Network policy helpers for sandbox containers."""

from __future__ import annotations

from typing import Any

from axon.logging import get_logger
from axon.sandbox.config import NetworkPolicy

logger = get_logger(__name__)

# Axon internal network name for container ↔ backend communication
AXON_NETWORK = "axon-sandbox-net"


def ensure_network(client: Any) -> str:
    """Ensure the Axon sandbox Docker network exists.

    Returns the network ID.
    """
    try:
        network = client.networks.get(AXON_NETWORK)
        return network.id
    except Exception:
        pass

    network = client.networks.create(
        AXON_NETWORK,
        driver="bridge",
        labels={"axon.managed": "true"},
    )
    logger.info("Created sandbox network: %s", AXON_NETWORK)
    return network.id


def apply_network_policy(
    container: Any,
    policy: NetworkPolicy,
    backend_url: str = "",
) -> None:
    """Apply network restrictions to a sandbox container.

    Uses iptables rules inside the container for domain filtering.
    For production use, consider a sidecar proxy (e.g., squid) instead.
    """
    if not policy.enabled:
        return

    if policy.allow_domains == ["*"] and not policy.block_domains:
        return  # No restrictions needed

    rules = _build_iptables_rules(policy, backend_url)
    if not rules:
        return

    script = " && ".join(rules)
    try:
        container.exec_run(
            ["sh", "-c", script],
            user="root",
        )
        logger.debug("Network policy applied to %s", container.short_id)
    except Exception as e:
        logger.warning("Failed to apply network policy: %s", e)


def _build_iptables_rules(policy: NetworkPolicy, backend_url: str) -> list[str]:
    """Generate iptables commands for the network policy."""
    rules: list[str] = []

    # Block specific domains
    for domain in policy.block_domains:
        rules.append(
            f"iptables -A OUTPUT -m string --string '{domain}' "
            f"--algo kmp -j DROP 2>/dev/null || true"
        )

    return rules
