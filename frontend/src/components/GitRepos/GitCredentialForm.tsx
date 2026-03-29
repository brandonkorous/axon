import { useState } from "react";
import { useCredentialStore } from "../../stores/credentialStore";

type CredType = "git_pat" | "git_ssh_key" | "git_app";

const CRED_LABELS: Record<CredType, string> = {
  git_pat: "Personal Access Token",
  git_ssh_key: "SSH Key",
  git_app: "GitHub App",
};

interface Props {
  onClose: () => void;
  onSaved: () => void;
}

export function GitCredentialForm({ onClose, onSaved }: Props) {
  const { createCredential } = useCredentialStore();
  const [credType, setCredType] = useState<CredType>("git_pat");
  const [label, setLabel] = useState("");
  const [token, setToken] = useState("");
  const [sshKey, setSshKey] = useState("");
  const [appId, setAppId] = useState("");
  const [installationId, setInstallationId] = useState("");
  const [appKey, setAppKey] = useState("");
  const [saving, setSaving] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);

    let secret = "";
    if (credType === "git_pat") {
      secret = token;
    } else if (credType === "git_ssh_key") {
      secret = sshKey;
    } else {
      secret = JSON.stringify({ app_id: appId, installation_id: installationId, private_key: appKey });
    }

    const ok = await createCredential(credType, secret, label || credType);
    setSaving(false);
    if (ok) onSaved();
  };

  const isValid = () => {
    if (credType === "git_pat") return token.trim().length > 0;
    if (credType === "git_ssh_key") return sshKey.trim().length > 0;
    return appId.trim().length > 0 && installationId.trim().length > 0 && appKey.trim().length > 0;
  };

  return (
    <div className="h-full flex flex-col">
      <div className="px-6 py-4 border-b border-neutral">
        <h1 className="text-xl font-bold text-base-content">Add Git Credential</h1>
        <p className="text-xs text-base-content/60 mt-1">Create authentication for private repositories</p>
      </div>

      <div className="flex-1 overflow-y-auto p-6">
        <form onSubmit={handleSubmit} className="max-w-xl mx-auto space-y-5">
          <fieldset>
            <legend className="label text-sm font-medium">Type</legend>
            <div className="flex gap-2 mt-1">
              {(Object.keys(CRED_LABELS) as CredType[]).map((t) => (
                <button key={t} type="button" onClick={() => setCredType(t)}
                  className={`badge badge-sm cursor-pointer ${credType === t ? "badge-accent" : "badge-ghost"}`}>
                  {CRED_LABELS[t]}
                </button>
              ))}
            </div>
          </fieldset>

          <div>
            <label htmlFor="cred-label" className="label text-sm font-medium">Label</label>
            <input id="cred-label" value={label} onChange={(e) => setLabel(e.target.value)}
              placeholder="e.g. GitHub CI Token" className="input input-sm w-full" />
          </div>

          {credType === "git_pat" && (
            <div>
              <label htmlFor="cred-token" className="label text-sm font-medium">Token</label>
              <input id="cred-token" type="password" value={token} onChange={(e) => setToken(e.target.value)}
                placeholder="ghp_..." className="input input-sm w-full" autoComplete="off" />
            </div>
          )}

          {credType === "git_ssh_key" && (
            <div>
              <label htmlFor="cred-ssh" className="label text-sm font-medium">Private Key</label>
              <textarea id="cred-ssh" value={sshKey} onChange={(e) => setSshKey(e.target.value)}
                placeholder="-----BEGIN OPENSSH PRIVATE KEY-----" rows={4} className="textarea textarea-sm w-full font-mono text-xs" />
            </div>
          )}

          {credType === "git_app" && (
            <>
              <div>
                <label htmlFor="cred-app-id" className="label text-sm font-medium">App ID</label>
                <input id="cred-app-id" value={appId} onChange={(e) => setAppId(e.target.value)}
                  placeholder="123456" className="input input-sm w-full" />
              </div>
              <div>
                <label htmlFor="cred-install-id" className="label text-sm font-medium">Installation ID</label>
                <input id="cred-install-id" value={installationId} onChange={(e) => setInstallationId(e.target.value)}
                  placeholder="78901234" className="input input-sm w-full" />
              </div>
              <div>
                <label htmlFor="cred-app-key" className="label text-sm font-medium">Private Key</label>
                <textarea id="cred-app-key" value={appKey} onChange={(e) => setAppKey(e.target.value)}
                  placeholder="-----BEGIN RSA PRIVATE KEY-----" rows={4} className="textarea textarea-sm w-full font-mono text-xs" />
              </div>
            </>
          )}

          <div className="flex gap-2 pt-2">
            <button type="submit" disabled={!isValid() || saving} className="btn btn-primary btn-sm flex-1">
              {saving ? <span className="loading loading-spinner loading-xs" /> : "Save Credential"}
            </button>
            <button type="button" onClick={onClose} className="btn btn-ghost btn-sm">Cancel</button>
          </div>
        </form>
      </div>
    </div>
  );
}
