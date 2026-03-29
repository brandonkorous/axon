"""Git init — credential injection and clone script for sandbox containers."""

from __future__ import annotations

CLONE_STRATEGIES = ("shallow", "full", "sparse")

# Bash script template injected into sandbox containers.
# Reads GIT_REPO_* env vars, clones repos, then scrubs credentials.
CLONE_SCRIPT = r'''#!/usr/bin/env bash
set -euo pipefail

count="${GIT_REPO_COUNT:-0}"
if [ "$count" -eq 0 ]; then
    echo "[git-init] No repositories configured"
    exit 0
fi

for i in $(seq 0 $((count - 1))); do
    url_var="GIT_REPO_${i}_URL"
    branch_var="GIT_REPO_${i}_BRANCH"
    strategy_var="GIT_REPO_${i}_STRATEGY"
    sparse_var="GIT_REPO_${i}_SPARSE_PATHS"
    auth_type_var="GIT_REPO_${i}_AUTH_TYPE"
    token_var="GIT_REPO_${i}_TOKEN"
    ssh_key_var="GIT_REPO_${i}_SSH_KEY"
    name_var="GIT_REPO_${i}_NAME"

    url="${!url_var}"
    branch="${!branch_var:-main}"
    strategy="${!strategy_var:-shallow}"
    sparse_paths="${!sparse_var:-}"
    auth_type="${!auth_type_var:-none}"
    name="${!name_var:-repo-$i}"

    dest="/workspace/$name"

    echo "[git-init] Cloning $url ($strategy) -> $dest"

    clone_args=()
    [ "$strategy" = "shallow" ] && clone_args+=(--depth=1)
    [ "$strategy" = "sparse" ] && clone_args+=(--sparse --filter=blob:none)
    clone_args+=(--branch "$branch")

    # Auth setup
    if [ "$auth_type" = "git_pat" ]; then
        token="${!token_var}"
        auth_url=$(echo "$url" | sed "s|https://|https://${token}@|")
        git clone "${clone_args[@]}" "$auth_url" "$dest"
    elif [ "$auth_type" = "git_ssh_key" ]; then
        ssh_key="${!ssh_key_var}"
        key_file=$(mktemp)
        echo "$ssh_key" > "$key_file"
        chmod 600 "$key_file"
        GIT_SSH_COMMAND="ssh -i $key_file -o StrictHostKeyChecking=no" \
            git clone "${clone_args[@]}" "$url" "$dest"
        rm -f "$key_file"
    else
        git clone "${clone_args[@]}" "$url" "$dest"
    fi

    # Sparse checkout paths
    if [ "$strategy" = "sparse" ] && [ -n "$sparse_paths" ]; then
        cd "$dest"
        IFS=',' read -ra paths <<< "$sparse_paths"
        for path in "${paths[@]}"; do
            git sparse-checkout add "$path"
        done
        cd /workspace
    fi

    echo "[git-init] Cloned $name successfully"
done

# Scrub credentials from environment
for i in $(seq 0 $((count - 1))); do
    unset "GIT_REPO_${i}_TOKEN" 2>/dev/null || true
    unset "GIT_REPO_${i}_SSH_KEY" 2>/dev/null || true
done

echo "[git-init] All repositories cloned"
'''


def build_clone_env(
    repos: list[dict],
    credentials: dict[str, dict],
) -> dict[str, str]:
    """Build environment variables for the clone script.

    Args:
        repos: List of repo configs with url, name, default_branch,
               clone_strategy, sparse_paths, auth_credential_id.
        credentials: Map of credential_id -> {provider, token/ssh_key/...}.

    Returns:
        Dict of env vars to inject into the container.
    """
    env: dict[str, str] = {"GIT_REPO_COUNT": str(len(repos))}

    for i, repo in enumerate(repos):
        prefix = f"GIT_REPO_{i}"
        env[f"{prefix}_URL"] = repo["url"]
        env[f"{prefix}_NAME"] = repo.get("name", f"repo-{i}")
        env[f"{prefix}_BRANCH"] = repo.get("default_branch", "main")
        env[f"{prefix}_STRATEGY"] = repo.get("clone_strategy", "shallow")

        sparse = repo.get("sparse_paths", [])
        if sparse:
            env[f"{prefix}_SPARSE_PATHS"] = ",".join(sparse)

        cred_id = repo.get("auth_credential_id")
        if cred_id and cred_id in credentials:
            cred = credentials[cred_id]
            provider = cred.get("provider", "")
            env[f"{prefix}_AUTH_TYPE"] = provider

            if provider == "git_pat":
                env[f"{prefix}_TOKEN"] = cred.get("token", "")
            elif provider == "git_ssh_key":
                env[f"{prefix}_SSH_KEY"] = cred.get("ssh_key", "")

    return env
