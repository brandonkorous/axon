import type { WorkerType } from "../../stores/workerStore";

interface Props {
  type: WorkerType;
  codebasePath: string;
  typeConfig: Record<string, string>;
  onCodebaseChange: (v: string) => void;
  onTypeConfigChange: (key: string, value: string) => void;
}

export function WorkerTypeConfig({
  type, codebasePath, typeConfig, onCodebaseChange, onTypeConfigChange,
}: Props) {
  switch (type) {
    case "code":
      return <CodeConfig path={codebasePath} onChange={onCodebaseChange} />;
    case "documents":
      return <FolderConfig label="Document Folder" path={codebasePath} onChange={onCodebaseChange} />;
    case "images":
      return <FolderConfig label="Image Folder" path={codebasePath} onChange={onCodebaseChange} />;
    case "shell":
      return <FolderConfig label="Working Directory" path={codebasePath} onChange={onCodebaseChange} />;
    case "email":
      return <EmailConfig config={typeConfig} onChange={onTypeConfigChange} />;
    case "browser":
      return <BrowserConfig config={typeConfig} onChange={onTypeConfigChange} />;
    default:
      return null;
  }
}

function CodeConfig({ path, onChange }: { path: string; onChange: (v: string) => void }) {
  return (
    <div>
      <label className="label text-sm font-medium">Codebase Path</label>
      <input
        value={path}
        onChange={(e) => onChange(e.target.value)}
        placeholder="e.g. D:\code\my-project"
        className="input input-sm w-full font-mono"
      />
      <p className="text-xs text-neutral-content mt-1">
        Local path to the git repository this worker operates on
      </p>
    </div>
  );
}

function FolderConfig({ label, path, onChange }: { label: string; path: string; onChange: (v: string) => void }) {
  return (
    <div>
      <label className="label text-sm font-medium">{label}</label>
      <input
        value={path}
        onChange={(e) => onChange(e.target.value)}
        placeholder="e.g. D:\documents\reports"
        className="input input-sm w-full font-mono"
      />
    </div>
  );
}

function EmailConfig({ config, onChange }: { config: Record<string, string>; onChange: (k: string, v: string) => void }) {
  return (
    <div className="space-y-3">
      <div>
        <label className="label text-sm font-medium">Email Provider</label>
        <select
          value={config.email_provider || "resend"}
          onChange={(e) => onChange("email_provider", e.target.value)}
          className="select select-sm w-full"
        >
          <option value="resend">Resend</option>
          <option value="gmail">Gmail</option>
          <option value="o365">Microsoft 365</option>
        </select>
      </div>
      <div>
        <label className="label text-sm font-medium">API Key / Access Token</label>
        <input
          type="password"
          value={config.api_key || ""}
          onChange={(e) => onChange("api_key", e.target.value)}
          placeholder="Enter API key..."
          className="input input-sm w-full font-mono"
        />
      </div>
      {config.email_provider === "resend" && (
        <div>
          <label className="label text-sm font-medium">From Address</label>
          <input
            value={config.from_address || ""}
            onChange={(e) => onChange("from_address", e.target.value)}
            placeholder="noreply@yourdomain.com"
            className="input input-sm w-full"
          />
        </div>
      )}
    </div>
  );
}

function BrowserConfig({ config, onChange }: { config: Record<string, string>; onChange: (k: string, v: string) => void }) {
  return (
    <div>
      <label className="label text-sm font-medium">Start URL</label>
      <input
        value={config.start_url || ""}
        onChange={(e) => onChange("start_url", e.target.value)}
        placeholder="https://example.com"
        className="input input-sm w-full font-mono"
      />
      <p className="text-xs text-neutral-content mt-1">
        Default URL to navigate to when starting browser tasks
      </p>
    </div>
  );
}
