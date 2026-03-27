import { useEffect, useState } from "react";
import { useAgentStore } from "../../stores/agentStore";
import { useIntegrationStore } from "../../stores/integrationStore";
import { usePluginStore } from "../../stores/pluginStore";
import { orgApiPath } from "../../stores/orgStore";

export function SkillsIntegrationsTab() {
  const { agents } = useAgentStore();
  const advisors = agents.filter((a) => a.type !== "external");

  return (
    <div className="space-y-6">
      <IntegrationsSection agents={advisors} />
      <div className="divider my-0" />
      <PluginsSection agents={advisors} />
    </div>
  );
}

function IntegrationsSection({ agents }: { agents: { id: string; name: string }[] }) {
  const { integrations, loading, fetchIntegrations, enableIntegration, disableIntegration } =
    useIntegrationStore();
  const [toggling, setToggling] = useState<string | null>(null);

  useEffect(() => {
    fetchIntegrations();
  }, [fetchIntegrations]);

  const handleToggle = async (agentId: string, name: string, enabled: boolean) => {
    setToggling(`${agentId}-${name}`);
    if (enabled) {
      await disableIntegration(agentId, name);
    } else {
      await enableIntegration(agentId, name);
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
      <div>
        <h4 className="text-sm font-semibold mb-2">Integrations</h4>
        <p className="text-xs text-base-content/60">No integrations available.</p>
      </div>
    );
  }

  return (
    <div>
      <h4 className="text-sm font-semibold mb-3">Integrations</h4>
      <div className="overflow-x-auto">
        <table className="table table-xs">
          <thead>
            <tr>
              <th className="text-xs">Integration</th>
              {agents.map((a) => (
                <th key={a.id} className="text-xs text-center">{a.name}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {integrations.map((intg) => (
              <tr key={intg.name}>
                <td className="font-medium text-xs">{intg.name}</td>
                {agents.map((a) => {
                  const enabled = intg.enabled_by.includes(a.id);
                  const key = `${a.id}-${intg.name}`;
                  return (
                    <td key={a.id} className="text-center">
                      {toggling === key ? (
                        <span className="loading loading-spinner loading-xs" />
                      ) : (
                        <input
                          type="checkbox"
                          className="checkbox checkbox-xs checkbox-primary"
                          checked={enabled}
                          onChange={() => handleToggle(a.id, intg.name, enabled)}
                        />
                      )}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function PluginsSection({ agents }: { agents: { id: string; name: string }[] }) {
  const { plugins, loading, fetchPlugins, enablePlugin, disablePlugin } = usePluginStore();
  const [details, setDetails] = useState<Record<string, string[]>>({});
  const [toggling, setToggling] = useState<string | null>(null);

  useEffect(() => {
    fetchPlugins();
  }, [fetchPlugins]);

  useEffect(() => {
    if (plugins.length === 0) return;
    const fetchDetails = async () => {
      const result: Record<string, string[]> = {};
      await Promise.all(
        plugins.map(async (s) => {
          try {
            const res = await fetch(orgApiPath(`plugins/${s.name}`));
            if (res.ok) {
              const data = await res.json();
              result[s.name] = data.agents_using || [];
            }
          } catch { /* skip */ }
        }),
      );
      setDetails(result);
    };
    fetchDetails();
  }, [plugins]);

  const handleToggle = async (pluginName: string, agentId: string, enabled: boolean) => {
    setToggling(`${agentId}-${pluginName}`);
    if (enabled) {
      await disablePlugin(pluginName, agentId);
    } else {
      await enablePlugin(pluginName, agentId);
    }
    // Refresh details
    try {
      const res = await fetch(orgApiPath(`plugins/${pluginName}`));
      if (res.ok) {
        const data = await res.json();
        setDetails((prev) => ({ ...prev, [pluginName]: data.agents_using || [] }));
      }
    } catch { /* skip */ }
    setToggling(null);
  };

  if (loading) {
    return (
      <div className="flex items-center gap-2 py-2">
        <span className="loading loading-spinner loading-xs" />
        <span className="text-xs text-base-content/60">Loading plugins...</span>
      </div>
    );
  }

  if (plugins.length === 0) {
    return (
      <div>
        <h4 className="text-sm font-semibold mb-2">Plugins</h4>
        <p className="text-xs text-base-content/60">No plugins available.</p>
      </div>
    );
  }

  return (
    <div>
      <h4 className="text-sm font-semibold mb-3">Plugins</h4>
      <div className="overflow-x-auto">
        <table className="table table-xs">
          <thead>
            <tr>
              <th className="text-xs">Plugin</th>
              {agents.map((a) => (
                <th key={a.id} className="text-xs text-center">{a.name}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {plugins.map((plugin) => (
              <tr key={plugin.name}>
                <td className="font-medium text-xs">{plugin.name}</td>
                {agents.map((a) => {
                  const agentsUsing = details[plugin.name] || [];
                  const enabled = agentsUsing.includes(a.id);
                  const key = `${a.id}-${plugin.name}`;
                  return (
                    <td key={a.id} className="text-center">
                      {toggling === key ? (
                        <span className="loading loading-spinner loading-xs" />
                      ) : (
                        <input
                          type="checkbox"
                          className="checkbox checkbox-xs checkbox-primary"
                          checked={enabled}
                          onChange={() => handleToggle(plugin.name, a.id, enabled)}
                        />
                      )}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
