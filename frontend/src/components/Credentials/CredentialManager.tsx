import { useState } from "react";
import { useCredentials, useCreateCredential, useDeleteCredential } from "../../hooks/useCredentials";

const PROVIDERS = [
  { value: "resend", label: "Resend (Email)" },
  { value: "discord", label: "Discord (Bot Token)" },
  { value: "slack_bot_token", label: "Slack (Bot Token)" },
  { value: "slack_app_token", label: "Slack (App Token)" },
  { value: "teams_app_id", label: "Teams (App ID)" },
  { value: "teams_app_secret", label: "Teams (App Secret)" },
  { value: "teams_organizer_id", label: "Teams (Organizer ID)" },
  { value: "zoom_account_id", label: "Zoom (Account ID)" },
  { value: "zoom_client_id", label: "Zoom (Client ID)" },
  { value: "zoom_client_secret", label: "Zoom (Client Secret)" },
] as const;

export function CredentialManager() {
  const { data: credentials = [], isLoading } = useCredentials();
  const createCredential = useCreateCredential();
  const deleteCredential = useDeleteCredential();
  const [adding, setAdding] = useState(false);
  const [provider, setProvider] = useState("resend");
  const [token, setToken] = useState("");
  const [saving, setSaving] = useState(false);

  const handleAdd = async () => {
    if (!token.trim()) return;
    setSaving(true);
    try {
      await createCredential.mutateAsync({ provider, access_token: token.trim() });
      setToken("");
      setAdding(false);
    } catch {
      // save failed
    }
    setSaving(false);
  };

  return (
    <div className="space-y-3">
      {isLoading ? (
        <div className="flex items-center gap-2 py-2">
          <span className="loading loading-spinner loading-xs" />
          <span className="text-xs text-base-content/60">Loading credentials...</span>
        </div>
      ) : credentials.length === 0 && !adding ? (
        <div className="text-xs text-base-content/60 py-1">
          No API keys configured. Add credentials to enable integrations.
        </div>
      ) : (
        <div className="space-y-2">
          {credentials.map((c) => (
            <div
              key={c.id}
              className="flex items-center justify-between bg-base-100 rounded px-3 py-2 border border-neutral/30"
            >
              <div className="flex items-center gap-3 min-w-0">
                <span className="badge badge-sm badge-outline font-mono">
                  {c.provider}
                </span>
                <span className="text-xs text-base-content/60 font-mono truncate">
                  {c.token_preview}
                </span>
              </div>
              <button
                onClick={() => deleteCredential.mutate(c.id)}
                className="btn btn-ghost btn-xs text-error"
                title="Remove credential"
              >
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} className="w-3.5 h-3.5">
                  <path d="M18 6L6 18M6 6l12 12" />
                </svg>
              </button>
            </div>
          ))}
        </div>
      )}

      {adding ? (
        <div className="space-y-2 bg-base-100 rounded p-3 border border-neutral/30">
          <select
            value={provider}
            onChange={(e) => setProvider(e.target.value)}
            className="select select-sm w-full"
          >
            {PROVIDERS.map((p) => (
              <option key={p.value} value={p.value}>{p.label}</option>
            ))}
          </select>
          <input
            type="password"
            value={token}
            onChange={(e) => setToken(e.target.value)}
            placeholder="Paste API key or token..."
            className="input input-sm w-full font-mono"
            autoFocus
          />
          <div className="flex gap-2">
            <button
              onClick={handleAdd}
              disabled={!token.trim() || saving}
              className="btn btn-primary btn-xs"
            >
              {saving ? <span className="loading loading-spinner loading-xs" /> : "Save"}
            </button>
            <button
              onClick={() => { setAdding(false); setToken(""); }}
              className="btn btn-ghost btn-xs"
            >
              Cancel
            </button>
          </div>
        </div>
      ) : (
        <button
          onClick={() => setAdding(true)}
          className="btn btn-ghost btn-xs text-primary"
        >
          + Add credential
        </button>
      )}
    </div>
  );
}
