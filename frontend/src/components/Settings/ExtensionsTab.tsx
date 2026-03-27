import { useEffect, useState } from "react";
import { useAgentStore } from "../../stores/agentStore";
import { usePluginStore } from "../../stores/pluginStore";
import { useSkillStore } from "../../stores/skillStore";
import { orgApiPath } from "../../stores/orgStore";

export function ExtensionsTab() {
  const { agents } = useAgentStore();
  const advisors = agents.filter((a) => a.type !== "external");

  return (
    <div className="space-y-6">
      <SkillsSection agents={advisors} />
      <div className="divider my-0" />
      <PluginsSection agents={advisors} />
    </div>
  );
}

// ---------------------------------------------------------------------------
// Skills toggle matrix
// ---------------------------------------------------------------------------

function SkillsSection({ agents }: { agents: { id: string; name: string }[] }) {
  const { skills, loading, fetchSkills, enableSkill, disableSkill } = useSkillStore();
  const [details, setDetails] = useState<Record<string, string[]>>({});
  const [toggling, setToggling] = useState<string | null>(null);

  useEffect(() => {
    fetchSkills();
  }, [fetchSkills]);

  useEffect(() => {
    if (skills.length === 0) return;
    const load = async () => {
      const result: Record<string, string[]> = {};
      await Promise.all(
        skills.map(async (s) => {
          try {
            const res = await fetch(orgApiPath(`skills/${s.name}`));
            if (res.ok) {
              const data = await res.json();
              result[s.name] = data.agents_using || [];
            }
          } catch { /* skip */ }
        }),
      );
      setDetails(result);
    };
    load();
  }, [skills]);

  const handleToggle = async (skillName: string, agentId: string, enabled: boolean) => {
    setToggling(`${agentId}-${skillName}`);
    if (enabled) {
      await disableSkill(skillName, agentId);
    } else {
      await enableSkill(skillName, agentId);
    }
    try {
      const res = await fetch(orgApiPath(`skills/${skillName}`));
      if (res.ok) {
        const data = await res.json();
        setDetails((prev) => ({ ...prev, [skillName]: data.agents_using || [] }));
      }
    } catch { /* skip */ }
    setToggling(null);
  };

  if (loading) return <LoadingRow label="skills" />;
  if (skills.length === 0) return <EmptyRow title="Skills" />;

  return (
    <div>
      <h4 className="text-sm font-semibold mb-1">Skills</h4>
      <p className="text-xs text-base-content/50 mb-3">
        Cognitive reasoning patterns injected into agent prompts
      </p>
      <ToggleMatrix
        items={skills.map((s) => s.name)}
        agents={agents}
        getEnabled={(name) => details[name] || []}
        toggling={toggling}
        onToggle={handleToggle}
      />
    </div>
  );
}

// ---------------------------------------------------------------------------
// Plugins toggle matrix (includes integrations — they're just plugins)
// ---------------------------------------------------------------------------

function PluginsSection({ agents }: { agents: { id: string; name: string }[] }) {
  const { plugins, loading, fetchPlugins, enablePlugin, disablePlugin } = usePluginStore();
  const [details, setDetails] = useState<Record<string, string[]>>({});
  const [toggling, setToggling] = useState<string | null>(null);

  useEffect(() => {
    fetchPlugins();
  }, [fetchPlugins]);

  useEffect(() => {
    if (plugins.length === 0) return;
    const load = async () => {
      const result: Record<string, string[]> = {};
      await Promise.all(
        plugins.map(async (p) => {
          try {
            const res = await fetch(orgApiPath(`plugins/${p.name}`));
            if (res.ok) {
              const data = await res.json();
              result[p.name] = data.agents_using || [];
            }
          } catch { /* skip */ }
        }),
      );
      setDetails(result);
    };
    load();
  }, [plugins]);

  const handleToggle = async (pluginName: string, agentId: string, enabled: boolean) => {
    setToggling(`${agentId}-${pluginName}`);
    if (enabled) {
      await disablePlugin(pluginName, agentId);
    } else {
      await enablePlugin(pluginName, agentId);
    }
    try {
      const res = await fetch(orgApiPath(`plugins/${pluginName}`));
      if (res.ok) {
        const data = await res.json();
        setDetails((prev) => ({ ...prev, [pluginName]: data.agents_using || [] }));
      }
    } catch { /* skip */ }
    setToggling(null);
  };

  if (loading) return <LoadingRow label="plugins" />;
  if (plugins.length === 0) return <EmptyRow title="Plugins" />;

  return (
    <div>
      <h4 className="text-sm font-semibold mb-1">Plugins</h4>
      <p className="text-xs text-base-content/50 mb-3">
        Tool-providing modules that extend agent capabilities
      </p>
      <ToggleMatrix
        items={plugins.map((p) => p.name)}
        labels={plugins.map((p) => ({
          name: p.name,
          badge: p.source === "integration" ? "integration" : undefined,
        }))}
        agents={agents}
        getEnabled={(name) => details[name] || []}
        toggling={toggling}
        onToggle={handleToggle}
      />
    </div>
  );
}

// ---------------------------------------------------------------------------
// Shared components
// ---------------------------------------------------------------------------

function ToggleMatrix({
  items,
  labels,
  agents,
  getEnabled,
  toggling,
  onToggle,
}: {
  items: string[];
  labels?: { name: string; badge?: string }[];
  agents: { id: string; name: string }[];
  getEnabled: (name: string) => string[];
  toggling: string | null;
  onToggle: (name: string, agentId: string, enabled: boolean) => void;
}) {
  return (
    <div className="overflow-x-auto">
      <table className="table table-xs">
        <thead>
          <tr>
            <th className="text-xs">Name</th>
            {agents.map((a) => (
              <th key={a.id} className="text-xs text-center">{a.name}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {items.map((name, i) => {
            const label = labels?.[i];
            return (
              <tr key={name}>
                <td className="font-medium text-xs">
                  <span className="flex items-center gap-1.5">
                    {name}
                    {label?.badge && (
                      <span className="badge badge-xs badge-ghost">{label.badge}</span>
                    )}
                  </span>
                </td>
                {agents.map((a) => {
                  const enabled = getEnabled(name).includes(a.id);
                  const key = `${a.id}-${name}`;
                  return (
                    <td key={a.id} className="text-center">
                      {toggling === key ? (
                        <span className="loading loading-spinner loading-xs" />
                      ) : (
                        <input
                          type="checkbox"
                          className="checkbox checkbox-xs checkbox-primary"
                          checked={enabled}
                          onChange={() => onToggle(name, a.id, enabled)}
                        />
                      )}
                    </td>
                  );
                })}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function LoadingRow({ label }: { label: string }) {
  return (
    <div className="flex items-center gap-2 py-2">
      <span className="loading loading-spinner loading-xs" />
      <span className="text-xs text-base-content/60">Loading {label}...</span>
    </div>
  );
}

function EmptyRow({ title }: { title: string }) {
  return (
    <div>
      <h4 className="text-sm font-semibold mb-2">{title}</h4>
      <p className="text-xs text-base-content/60">No {title.toLowerCase()} available.</p>
    </div>
  );
}
