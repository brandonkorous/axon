import { useEffect, useState } from "react";
import { useGitRepoStore, type GitRepo } from "../../stores/gitRepoStore";
import { useCredentialStore } from "../../stores/credentialStore";
import { GitRepoForm } from "./GitRepoForm";

const STRATEGY_BADGE: Record<string, string> = {
  shallow: "badge-info",
  full: "badge-warning",
  sparse: "badge-accent",
};

export function GitRepoList() {
  const { repos, loading, fetchRepos, deleteRepo } = useGitRepoStore();
  const { credentials, fetchCredentials } = useCredentialStore();
  const [editingRepo, setEditingRepo] = useState<GitRepo | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState<string | null>(null);

  useEffect(() => {
    fetchRepos();
    fetchCredentials();
  }, [fetchRepos, fetchCredentials]);

  const handleDelete = async (id: string) => {
    await deleteRepo(id);
    setConfirmDelete(null);
  };

  const handleFormClose = () => {
    setShowForm(false);
    setEditingRepo(null);
  };

  const credentialLabel = (id: string | null) => {
    if (!id) return null;
    const cred = credentials.find((c) => c.id === id);
    return cred?.label || cred?.provider || "linked";
  };

  if (showForm || editingRepo) {
    return (
      <GitRepoForm
        repo={editingRepo}
        onClose={handleFormClose}
        onSaved={handleFormClose}
      />
    );
  }

  return (
    <div className="h-full flex flex-col">
      <div className="px-6 py-4 border-b border-neutral flex items-start justify-between">
        <div>
          <h1 className="text-xl font-bold text-base-content">Git Repositories</h1>
          <p className="text-xs text-base-content/60 mt-1">
            Configure repositories for agents to clone into sandboxes
          </p>
        </div>
        <button onClick={() => setShowForm(true)} className="btn btn-primary btn-sm">
          Add Repository
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-6">
        {loading && repos.length === 0 ? (
          <div className="flex items-center justify-center h-32">
            <span className="loading loading-spinner loading-md text-primary" />
          </div>
        ) : repos.length === 0 ? (
          <p className="text-sm text-base-content/60 text-center mt-12">
            No repositories configured yet
          </p>
        ) : (
          <div className="max-w-2xl mx-auto space-y-2">
            {repos.map((repo) => (
              <div key={repo.id}>
                <RepoCard
                  repo={repo}
                  credentialLabel={credentialLabel(repo.auth_credential_id)}
                  onEdit={() => setEditingRepo(repo)}
                  onDelete={() => setConfirmDelete(repo.id)}
                />
                {confirmDelete === repo.id && (
                  <div className="flex items-center gap-2 mt-1 ml-4">
                    <span className="text-xs text-error">Remove this repository?</span>
                    <button onClick={() => handleDelete(repo.id)} className="btn btn-error btn-xs">
                      Yes, remove
                    </button>
                    <button onClick={() => setConfirmDelete(null)} className="btn btn-ghost btn-xs">
                      Cancel
                    </button>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function RepoCard({
  repo, credentialLabel, onEdit, onDelete,
}: {
  repo: GitRepo; credentialLabel: string | null; onEdit: () => void; onDelete: () => void;
}) {
  return (
    <div className="card bg-base-300 border border-neutral hover:border-primary/30 transition-colors">
      <div className="card-body p-4 flex-row items-center gap-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <p className="text-sm font-medium">{repo.name}</p>
            <span className={`badge badge-xs ${STRATEGY_BADGE[repo.clone_strategy]}`}>
              {repo.clone_strategy}
            </span>
            {credentialLabel && (
              <span className="badge badge-xs badge-ghost">{credentialLabel}</span>
            )}
            {!repo.auth_credential_id && (
              <span className="badge badge-xs badge-ghost">public</span>
            )}
          </div>
          <p className="text-xs text-base-content/60 truncate mt-0.5 font-mono">{repo.url}</p>
          <p className="text-xs text-base-content/40 mt-0.5">branch: {repo.default_branch}</p>
        </div>
        <div className="flex items-center gap-1">
          <button onClick={onEdit} className="btn btn-ghost btn-xs" aria-label={`Edit ${repo.name}`}>
            Edit
          </button>
          <button onClick={onDelete} className="btn btn-ghost btn-xs text-error" aria-label={`Delete ${repo.name}`}>
            Delete
          </button>
        </div>
      </div>
    </div>
  );
}
