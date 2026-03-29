"""Kubernetes volume helpers — translate sandbox mounts to k8s volume specs."""

from __future__ import annotations

from typing import Any


def build_volumes_and_mounts(
    org_id: str,
    agent_id: str,
    instance_id: str,
    runner_dir: str,
    workspace_dir: str,
    extra_mounts: list[str],
    storage_class: str = "standard",
    init_script: str | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Build k8s volume and volumeMount specs for a sandbox pod.

    Returns (volumes, volume_mounts) as plain dicts ready for V1PodSpec.
    """
    volumes: list[dict[str, Any]] = []
    mounts: list[dict[str, Any]] = []

    # Runner directory — ConfigMap or PVC depending on content
    runner_vol_name = f"runner-{agent_id}-{instance_id[:8]}"
    volumes.append({
        "name": runner_vol_name,
        "persistentVolumeClaim": {"claimName": runner_vol_name},
    })
    mounts.append({
        "name": runner_vol_name,
        "mountPath": "/runner",
    })

    # Workspace — PVC for agent workspace
    workspace_vol_name = f"workspace-{org_id}-{agent_id}"
    volumes.append({
        "name": workspace_vol_name,
        "persistentVolumeClaim": {"claimName": workspace_vol_name},
    })
    mounts.append({
        "name": workspace_vol_name,
        "mountPath": "/workspace",
    })

    # Git init script — ConfigMap volume
    if init_script:
        cm_name = f"git-init-{agent_id}-{instance_id[:8]}"
        volumes.append({
            "name": "git-init-script",
            "configMap": {
                "name": cm_name,
                "defaultMode": 0o755,
                "items": [{"key": "git_init.sh", "path": "git_init.sh"}],
            },
        })
        mounts.append({
            "name": "git-init-script",
            "mountPath": "/runner/git_init.sh",
            "subPath": "git_init.sh",
        })

    # Extra mounts — in k8s these are PVC references: "pvc-name:/container/path"
    for i, spec in enumerate(extra_mounts):
        parts = spec.split(":", 1)
        if len(parts) != 2:
            continue
        pvc_name, container_path = parts[0], parts[1]
        vol_name = f"extra-{i}"
        volumes.append({
            "name": vol_name,
            "persistentVolumeClaim": {"claimName": pvc_name},
        })
        mounts.append({
            "name": vol_name,
            "mountPath": container_path,
        })

    return volumes, mounts


def pvc_spec(
    name: str,
    namespace: str,
    storage_mb: int,
    storage_class: str = "standard",
    labels: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Build a PVC spec dict for creating via the k8s API."""
    return {
        "apiVersion": "v1",
        "kind": "PersistentVolumeClaim",
        "metadata": {
            "name": name,
            "namespace": namespace,
            "labels": labels or {},
        },
        "spec": {
            "accessModes": ["ReadWriteOnce"],
            "storageClassName": storage_class,
            "resources": {
                "requests": {"storage": f"{storage_mb}Mi"},
            },
        },
    }
