"""Mount path validation — prevent dangerous host mounts in sandboxes."""

from __future__ import annotations

from pathlib import PurePosixPath

# Exact paths that are always blocked
BLOCKED_EXACT: frozenset[str] = frozenset({
    "/var/run/docker.sock",
    "/var/run/docker",
})

# Prefix-based blocks (normalized to forward-slash lowercase)
BLOCKED_PREFIXES: tuple[str, ...] = (
    "/etc", "/usr", "/var", "/boot", "/sys", "/proc", "/dev",
    "/sbin", "/bin", "/lib", "/lib64", "/opt",
    "/root",
    # Windows system dirs (normalized from C:\ to /c/)
    "/c/windows", "/c/program files", "/c/program files (x86)",
    "/c/programdata", "/c/recovery", "/c/$recycle.bin",
    "/d/windows",
)

# Prefixes allowed only if path goes deep enough
MIN_DEPTH_PATHS: dict[str, int] = {
    "/home": 3,      # /home/user/something
    "/c/users": 4,   # /c/users/name/something
    "/d/users": 4,
}


def normalize_path(path: str) -> str:
    """Normalize a path for validation: resolve .., lowercase, forward slashes.

    Handles Windows drive letters: C:\\foo -> /c/foo
    """
    p = path.replace("\\", "/")
    # Handle Windows drive letters: C:/ -> /c/
    if len(p) >= 2 and p[1] == ":" and p[0].isalpha():
        p = f"/{p[0].lower()}{p[2:]}"
    # Resolve .. and normalize
    p = str(PurePosixPath(p))
    p = p.lower().rstrip("/")
    return p or "/"


def _path_depth(path: str) -> int:
    """Count path components (/ = 1, /home = 2, /home/user = 3)."""
    return len([part for part in path.split("/") if part])


def validate_mount_path(
    host_path: str,
    axon_data_dirs: list[str] | None = None,
) -> tuple[bool, str]:
    """Validate a host mount path. Returns (is_valid, error_message)."""
    if not host_path or not host_path.strip():
        return False, "Mount path cannot be empty"

    normalized = normalize_path(host_path)

    # Block root / drive root
    if normalized in ("/", "/c", "/d", "/e", "/f"):
        return False, "Cannot mount root or drive root directories"

    # Block exact matches
    if normalized in BLOCKED_EXACT:
        return False, f"Path is blocked: {host_path}"

    # Block system prefixes
    for prefix in BLOCKED_PREFIXES:
        if normalized == prefix or normalized.startswith(prefix + "/"):
            return False, f"Cannot mount system directory: {host_path}"

    # Check minimum depth for sensitive prefixes
    for prefix, min_depth in MIN_DEPTH_PATHS.items():
        if normalized.startswith(prefix):
            if _path_depth(normalized) < min_depth:
                return False, (
                    f"Path too broad — must be at least {min_depth} levels deep "
                    f"(e.g., {prefix}/user/project)"
                )

    # Block Axon's own directories
    if axon_data_dirs:
        for axon_dir in axon_data_dirs:
            norm_axon = normalize_path(axon_dir)
            if normalized == norm_axon or normalized.startswith(norm_axon + "/"):
                return False, f"Cannot mount Axon data directory: {host_path}"

    # Must be absolute path
    raw = host_path.replace("\\", "/")
    is_abs = raw.startswith("/") or (
        len(raw) >= 3 and raw[1] == ":" and raw[2] in "/\\"
    )
    if not is_abs:
        return False, "Mount path must be absolute"

    return True, ""


def validate_mount_spec(
    mount_spec: str,
    axon_data_dirs: list[str] | None = None,
) -> tuple[bool, str]:
    """Validate a 'host_path:container_path' mount spec."""
    parts = mount_spec.split(":", 1)

    # Handle Windows paths like C:\foo:/container — re-split on the second colon
    if len(parts) == 2 and len(parts[0]) == 1 and parts[0].isalpha():
        remainder = parts[1]
        colon_idx = remainder.find(":")
        if colon_idx > 0:
            host_path = parts[0] + ":" + remainder[:colon_idx]
        else:
            return False, "Invalid mount spec — expected host_path:container_path"
    elif len(parts) == 2:
        host_path = parts[0]
    else:
        return False, "Invalid mount spec — expected host_path:container_path"

    return validate_mount_path(host_path, axon_data_dirs)
