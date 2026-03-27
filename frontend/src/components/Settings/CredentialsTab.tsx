import { CredentialManager } from "../Credentials/CredentialManager";

export function CredentialsTab() {
  return (
    <div className="space-y-6">
      <div>
        <h4 className="text-sm font-semibold mb-1">Communication Keys</h4>
        <p className="text-xs text-base-content/60 mb-3">
          API keys for email (Resend) and Discord integrations.
        </p>
        <CredentialManager />
      </div>

      <div className="divider my-0" />

      <div>
        <h4 className="text-sm font-semibold mb-1">LLM Provider Keys</h4>
        <p className="text-xs text-base-content/60 mb-3">
          API keys for language model providers. Configure these in your
          environment variables or <code className="text-xs">.env</code> file.
        </p>
        <div className="space-y-2">
          <EnvKeyRow label="Anthropic" envVar="ANTHROPIC_API_KEY" />
          <EnvKeyRow label="OpenAI" envVar="OPENAI_API_KEY" />
          <EnvKeyRow label="Ollama URL" envVar="OLLAMA_BASE_URL" />
        </div>
      </div>
    </div>
  );
}

function EnvKeyRow({ label, envVar }: { label: string; envVar: string }) {
  return (
    <div className="flex items-center justify-between bg-base-100 rounded px-3 py-2 border border-neutral/30">
      <div className="flex items-center gap-3 min-w-0">
        <span className="badge badge-sm badge-outline font-mono">{label}</span>
        <span className="text-xs text-base-content/60 font-mono">{envVar}</span>
      </div>
      <span className="text-xs text-base-content/40">env</span>
    </div>
  );
}
