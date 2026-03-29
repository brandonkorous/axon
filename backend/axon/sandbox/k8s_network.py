"""Kubernetes NetworkPolicy helpers for sandbox pod isolation."""

from __future__ import annotations

from typing import Any

from axon.sandbox.config import NetworkPolicy


def build_network_policy(
    pod_name: str,
    namespace: str,
    policy: NetworkPolicy,
    backend_service: str = "axon-backend",
    backend_namespace: str = "axon",
) -> dict[str, Any] | None:
    """Build a k8s NetworkPolicy spec for a sandbox pod.

    Returns None if no restrictions are needed (network enabled + allow all).
    """
    if not policy.enabled:
        return _deny_all_egress(pod_name, namespace)

    if policy.allow_domains == ["*"] and not policy.block_domains:
        if policy.allow_internal:
            return None  # No restrictions needed
        return _deny_all_egress(pod_name, namespace)

    return _restricted_egress(
        pod_name, namespace, policy,
        backend_service, backend_namespace,
    )


def _deny_all_egress(pod_name: str, namespace: str) -> dict[str, Any]:
    """NetworkPolicy that blocks all outbound traffic."""
    return {
        "apiVersion": "networking.k8s.io/v1",
        "kind": "NetworkPolicy",
        "metadata": {
            "name": f"{pod_name}-deny-egress",
            "namespace": namespace,
        },
        "spec": {
            "podSelector": {
                "matchLabels": {"axon.sandbox.pod": pod_name},
            },
            "policyTypes": ["Egress"],
            "egress": [],  # Empty = deny all
        },
    }


def _restricted_egress(
    pod_name: str,
    namespace: str,
    policy: NetworkPolicy,
    backend_service: str,
    backend_namespace: str,
) -> dict[str, Any]:
    """NetworkPolicy with selective egress rules."""
    egress_rules: list[dict[str, Any]] = []

    # Always allow DNS resolution
    egress_rules.append({
        "ports": [{"protocol": "UDP", "port": 53}, {"protocol": "TCP", "port": 53}],
    })

    # Allow Axon backend access if configured
    if policy.allow_internal:
        egress_rules.append({
            "to": [{
                "namespaceSelector": {"matchLabels": {"kubernetes.io/metadata.name": backend_namespace}},
                "podSelector": {"matchLabels": {"app": backend_service}},
            }],
            "ports": [{"protocol": "TCP", "port": 8000}],
        })

    # Allow general HTTP/HTTPS outbound (domain filtering requires a CNI
    # plugin like Calico with DNS policy — k8s NetworkPolicy alone can't
    # filter by domain name, only by IP/CIDR. We allow broad egress here
    # and document that domain-level filtering needs Calico or a proxy.)
    if policy.allow_domains == ["*"]:
        egress_rules.append({
            "ports": [{"protocol": "TCP", "port": 443}, {"protocol": "TCP", "port": 80}],
        })

    return {
        "apiVersion": "networking.k8s.io/v1",
        "kind": "NetworkPolicy",
        "metadata": {
            "name": f"{pod_name}-egress",
            "namespace": namespace,
        },
        "spec": {
            "podSelector": {
                "matchLabels": {"axon.sandbox.pod": pod_name},
            },
            "policyTypes": ["Egress"],
            "egress": egress_rules,
        },
    }
