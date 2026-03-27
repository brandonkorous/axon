import { useEffect, useState } from "react";
import {
  useIntegrationStore,
  type IntegrationInfo,
  type IntegrationStatus,
} from "../../stores/integrationStore";

const INTEGRATION_ICONS: Record<string, string> = {
  google_calendar: "📅",
  linear: "🔲",
};

interface IntegrationPanelProps {
  agentId: string;
}

export function IntegrationPanel({ agentId }: IntegrationPanelProps) {
  const { integrations, loading, fetchIntegrations, enableIntegration, disableIntegration } =
    useIntegrationStore();
  const [statuses, setStatuses] = useState<Record<string, IntegrationStatus>>({});
  const [toggling, setToggling] = useState<string | null>(null);
  const { fetchIntegrationStatus } = useIntegrationStore();

  useEffect(() => {
    fetchIntegrations();
  }, [fetchIntegrations]);

  useEffect(() => {
    const loadStatuses = async () => {
      const results: Record<string, IntegrationStatus> = {};
      for (const integration of integrations) {
        const status = await fetchIntegrationStatus(integration.name);
        if (status) results[integration.name] = status;
      }
      setStatuses(results);
    };
    if (integrations.length > 0) loadStatuses();
  }, [integrations, fetchIntegrationStatus]);

  const handleToggle = async (integration: IntegrationInfo) => {
    setToggling(integration.name);
    const isEnabled = integration.enabled_by.includes(agentId);
    if (isEnabled) {
      await disableIntegration(agentId, integration.name);
    } else {
      await enableIntegration(agentId, integration.name);
    }
    setToggling(null);
  };

  if (loading) {
    return (
      <div className="flex items-center gap-2 py-2">
        <span className="loading loading-spinner loading-xs" />
        <span className="text-xs text-base-content/60">Loading integrations...</span>
      </div>
    );
  }

  if (integrations.length === 0) {
    return (
      <div className="text-xs text-base-content/60 py-1">
        No integrations available. Add integration modules to enable external services.
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {integrations.map((integration) => {
        const isEnabled = integration.enabled_by.includes(agentId);
        const status = statuses[integration.name];
        const icon = INTEGRATION_ICONS[integration.name] || "🔌";

        return (
          <div
            key={integration.name}
            className="flex items-center justify-between bg-base-100 rounded px-3 py-2 border border-neutral/30"
          >
            <div className="flex items-center gap-3 min-w-0">
              <span className="text-base">{icon}</span>
              <div className="min-w-0">
                <div className="text-sm font-medium">{integration.name.replace(/_/g, " ")}</div>
                <div className="text-xs text-base-content/60 truncate">
                  {integration.description} · {integration.tool_count} tool
                  {integration.tool_count !== 1 ? "s" : ""}
                </div>
                {status && (
                  <div className="flex items-center gap-1 mt-0.5">
                    <span
                      className={`w-1.5 h-1.5 rounded-full ${
                        status.credentials_configured ? "bg-success" : "bg-warning"
                      }`}
                    />
                    <span className="text-xs text-base-content/50">
                      {status.credentials_configured ? "Credentials configured" : "No credentials"}
                    </span>
                  </div>
                )}
              </div>
            </div>
            <label className="swap">
              <input
                type="checkbox"
                checked={isEnabled}
                onChange={() => handleToggle(integration)}
                disabled={toggling === integration.name}
              />
              <div
                className={`btn btn-xs ${
                  isEnabled ? "btn-primary" : "btn-ghost border-neutral/30"
                }`}
              >
                {toggling === integration.name ? (
                  <span className="loading loading-spinner loading-xs" />
                ) : isEnabled ? (
                  "Enabled"
                ) : (
                  "Enable"
                )}
              </div>
            </label>
          </div>
        );
      })}
    </div>
  );
}
