import { useEffect, useState } from "react";
import {
  useIntegrationStore,
  type IntegrationDetail as IntegrationDetailType,
  type IntegrationStatus,
} from "../../stores/integrationStore";

interface IntegrationDetailProps {
  name: string;
  onClose?: () => void;
}

export function IntegrationDetail({ name, onClose }: IntegrationDetailProps) {
  const { fetchIntegrationDetail, fetchIntegrationStatus } = useIntegrationStore();
  const [detail, setDetail] = useState<IntegrationDetailType | null>(null);
  const [status, setStatus] = useState<IntegrationStatus | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      const [d, s] = await Promise.all([
        fetchIntegrationDetail(name),
        fetchIntegrationStatus(name),
      ]);
      setDetail(d);
      setStatus(s);
      setLoading(false);
    };
    load();
  }, [name, fetchIntegrationDetail, fetchIntegrationStatus]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <span className="loading loading-spinner loading-sm" />
      </div>
    );
  }

  if (!detail) {
    return (
      <div className="text-sm text-base-content/60 py-4">
        Integration not found: {name}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h3 className="text-lg font-semibold capitalize">
            {detail.name.replace(/_/g, " ")}
          </h3>
          <p className="text-sm text-base-content/60">{detail.description}</p>
        </div>
        {onClose && (
          <button onClick={onClose} className="btn btn-ghost btn-xs">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} className="w-4 h-4">
              <path d="M18 6L6 18M6 6l12 12" />
            </svg>
          </button>
        )}
      </div>

      {/* Credential Status */}
      <div className="bg-base-100 rounded-lg p-3 border border-neutral/30">
        <div className="text-xs font-medium text-base-content/70 uppercase tracking-wide mb-2">
          Credential Status
        </div>
        <div className="flex items-center gap-2">
          <span
            className={`w-2 h-2 rounded-full ${
              status?.credentials_configured ? "bg-success" : "bg-warning"
            }`}
          />
          <span className="text-sm">
            {status?.credentials_configured
              ? "Credentials configured"
              : "No credentials — add via Settings > Credentials"}
          </span>
        </div>
      </div>

      {/* Required Scopes */}
      {detail.required_scopes.length > 0 && (
        <div>
          <div className="text-xs font-medium text-base-content/70 uppercase tracking-wide mb-1">
            Required Scopes
          </div>
          <div className="flex flex-wrap gap-1">
            {detail.required_scopes.map((scope) => (
              <span key={scope} className="badge badge-sm badge-outline font-mono">
                {scope}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Tools */}
      <div>
        <div className="text-xs font-medium text-base-content/70 uppercase tracking-wide mb-2">
          Tools ({detail.tools.length})
        </div>
        <div className="space-y-1.5">
          {detail.tools.map((tool) => (
            <div
              key={tool.name}
              className="bg-base-100 rounded px-3 py-2 border border-neutral/20"
            >
              <div className="text-sm font-mono font-medium">{tool.name}</div>
              <div className="text-xs text-base-content/60">{tool.description}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Enabled By */}
      <div>
        <div className="text-xs font-medium text-base-content/70 uppercase tracking-wide mb-1">
          Enabled by Agents
        </div>
        {detail.enabled_by.length > 0 ? (
          <div className="flex flex-wrap gap-1">
            {detail.enabled_by.map((agentId) => (
              <span key={agentId} className="badge badge-sm badge-primary badge-outline">
                {agentId}
              </span>
            ))}
          </div>
        ) : (
          <span className="text-xs text-base-content/50">Not enabled by any agents</span>
        )}
      </div>
    </div>
  );
}
