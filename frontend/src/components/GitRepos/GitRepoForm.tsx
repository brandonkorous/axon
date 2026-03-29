import { useEffect, useState } from "react";
import { useGitRepoStore, type CloneStrategy, type GitRepo } from "../../stores/gitRepoStore";
import { useCredentialStore } from "../../stores/credentialStore";
import { GitCredentialForm } from "./GitCredentialForm";

const GIT_CREDENTIAL_TYPES = ["git_pat", "git_ssh_key", "git_app"];

interface Props {
  repo: GitRepo | null;
  onClose: () => void;
  onSaved: () => void;
}

export function GitRepoForm({ repo, onClose, onSaved }: Props) {
  const { createRepo, updateRepo } = useGitRepoStore();
  const { credentials, fetchCredentials } = useCredentialStore();

  const [url, setUrl] = useState(repo?.url || "");
  const [name, setName] = useState(repo?.name || "");
  const [branch, setBranch] = useState(repo?.default_branch || "main");
  const [credentialId, setCredentialId] = useState<string>(repo?.auth_credential_id || "");
  const [strategy, setStrategy] = useState<CloneStrategy>(repo?.clone_strategy || "shallow");
  const [sparsePaths, setSparsePaths] = useState(repo?.sparse_paths?.join("\n") || "");
  const [saving, setSaving] = useState(false);
  const [showCredForm, setShowCredForm] = useState(false);

  useEffect(() => {
    fetchCredentials();
  }, [fetchCredentials]);

  const gitCredentials = credentials.filter((c) => GIT_CREDENTIAL_TYPES.includes(c.provider));

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!url.trim() || !name.trim()) return;
    setSaving(true);

    const data = {
      url: url.trim(),
      name: name.trim(),
      default_branch: branch.trim() || "main",
      auth_credential_id: credentialId || null,
      clone_strategy: strategy,
      sparse_paths: strategy === "sparse"
        ? sparsePaths.split(/[,\n]/).map((p) => p.trim()).filter(Boolean)
        : [],
    };

    const ok = repo
      ? await updateRepo(repo.id, data)
      : await createRepo(data);

    setSaving(false);
    if (ok) onSaved();
  };

  const handleCredentialCreated = () => {
    setShowCredForm(false);
    fetchCredentials();
  };

  if (showCredForm) {
    return <GitCredentialForm onClose={() => setShowCredForm(false)} onSaved={handleCredentialCreated} />;
  }

  return (
    <div className="h-full flex flex-col">
      <div className="px-6 py-4 border-b border-neutral">
        <h1 className="text-xl font-bold text-base-content">
          {repo ? "Edit Repository" : "Add Repository"}
        </h1>
        <p className="text-xs text-base-content/60 mt-1">
          {repo ? "Update repository configuration" : "Configure a new git repository"}
        </p>
      </div>

      <div className="flex-1 overflow-y-auto p-6">
        <form onSubmit={handleSubmit} className="max-w-xl mx-auto space-y-5">
          <div>
            <label htmlFor="repo-url" className="label text-sm font-medium">URL</label>
            <input id="repo-url" autoFocus value={url} onChange={(e) => setUrl(e.target.value)}
              placeholder="https://github.com/org/repo.git" className="input input-sm w-full" required />
          </div>

          <div>
            <label htmlFor="repo-name" className="label text-sm font-medium">Name</label>
            <input id="repo-name" value={name} onChange={(e) => setName(e.target.value)}
              placeholder="Display name" className="input input-sm w-full" required />
          </div>

          <div>
            <label htmlFor="repo-branch" className="label text-sm font-medium">Default Branch</label>
            <input id="repo-branch" value={branch} onChange={(e) => setBranch(e.target.value)}
              placeholder="main" className="input input-sm w-full" />
          </div>

          <div>
            <label htmlFor="repo-cred" className="label text-sm font-medium">Credential</label>
            <div className="flex items-center gap-2">
              <select id="repo-cred" value={credentialId} onChange={(e) => setCredentialId(e.target.value)}
                className="select select-sm flex-1">
                <option value="">None (public repo)</option>
                {gitCredentials.map((c) => (
                  <option key={c.id} value={c.id}>{c.label || c.provider} ({c.token_preview})</option>
                ))}
              </select>
              <button type="button" onClick={() => setShowCredForm(true)} className="btn btn-ghost btn-sm">
                + Add
              </button>
            </div>
          </div>

          <fieldset>
            <legend className="label text-sm font-medium">Clone Strategy</legend>
            <div className="flex gap-4 mt-1">
              {(["shallow", "full", "sparse"] as const).map((s) => (
                <label key={s} className="flex items-center gap-2 cursor-pointer">
                  <input type="radio" name="strategy" className="radio radio-sm radio-primary"
                    checked={strategy === s} onChange={() => setStrategy(s)} />
                  <span className="text-sm capitalize">{s}</span>
                </label>
              ))}
            </div>
            <p className="text-xs text-base-content/60 mt-1">
              {strategy === "shallow" && "Fast clone with limited history"}
              {strategy === "full" && "Complete clone with full history"}
              {strategy === "sparse" && "Clone only specific paths"}
            </p>
          </fieldset>

          {strategy === "sparse" && (
            <div>
              <label htmlFor="sparse-paths" className="label text-sm font-medium">Sparse Paths</label>
              <textarea id="sparse-paths" value={sparsePaths} onChange={(e) => setSparsePaths(e.target.value)}
                placeholder={"src/\ndocs/"} rows={3} className="textarea textarea-sm w-full" />
              <p className="text-xs text-base-content/60 mt-1">One path per line or comma-separated</p>
            </div>
          )}

          <div className="flex gap-2 pt-2">
            <button type="submit" disabled={!url.trim() || !name.trim() || saving} className="btn btn-primary btn-sm flex-1">
              {saving ? <span className="loading loading-spinner loading-xs" /> : repo ? "Save Changes" : "Add Repository"}
            </button>
            <button type="button" onClick={onClose} className="btn btn-ghost btn-sm">Cancel</button>
          </div>
        </form>
      </div>
    </div>
  );
}
