import { useEffect } from "react";
import { useGitRepoStore, type GitRepo } from "../../stores/gitRepoStore";

const STRATEGY_BADGE: Record<string, string> = {
  shallow: "badge-info",
  full: "badge-warning",
  sparse: "badge-accent",
};

interface Props {
  selectedRepoIds: string[];
  onChange: (repoIds: string[]) => void;
}

export function WorkerRepoSelect({ selectedRepoIds, onChange }: Props) {
  const { repos, loading, fetchRepos } = useGitRepoStore();

  useEffect(() => {
    fetchRepos();
  }, [fetchRepos]);

  const toggle = (id: string) => {
    onChange(
      selectedRepoIds.includes(id)
        ? selectedRepoIds.filter((r) => r !== id)
        : [...selectedRepoIds, id],
    );
  };

  if (loading && repos.length === 0) {
    return <span className="loading loading-spinner loading-xs text-primary" />;
  }

  if (repos.length === 0) {
    return (
      <p className="text-xs text-base-content/60">
        No repositories configured.{" "}
        <a href="/repos" className="link link-primary">Add one</a>
      </p>
    );
  }

  return (
    <div className="space-y-1.5">
      {selectedRepoIds.length > 0 && (
        <div className="flex flex-wrap gap-1 mb-2">
          {selectedRepoIds.map((id) => {
            const repo = repos.find((r) => r.id === id);
            return repo ? (
              <span key={id} className="badge badge-sm badge-accent gap-1">
                {repo.name}
                <button type="button" onClick={() => toggle(id)} className="text-xs" aria-label={`Remove ${repo.name}`}>
                  x
                </button>
              </span>
            ) : null;
          })}
        </div>
      )}

      {repos.map((repo) => (
        <RepoOption key={repo.id} repo={repo} selected={selectedRepoIds.includes(repo.id)} onToggle={() => toggle(repo.id)} />
      ))}
    </div>
  );
}

function RepoOption({ repo, selected, onToggle }: { repo: GitRepo; selected: boolean; onToggle: () => void }) {
  return (
    <label className="flex items-center gap-3 px-3 py-2 rounded bg-base-100 border border-neutral/30 cursor-pointer hover:border-primary/30 transition-colors">
      <input type="checkbox" className="checkbox checkbox-sm checkbox-primary" checked={selected} onChange={onToggle} />
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium">{repo.name}</span>
          <span className={`badge badge-xs ${STRATEGY_BADGE[repo.clone_strategy]}`}>{repo.clone_strategy}</span>
        </div>
        <p className="text-xs text-base-content/60 truncate font-mono">{repo.url}</p>
      </div>
    </label>
  );
}
