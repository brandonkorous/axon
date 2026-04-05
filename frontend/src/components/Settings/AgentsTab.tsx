import { useEffect, useState } from "react";
import { useAgents, useUpdatePersona } from "../../hooks/useAgents";
import type { AgentInfo } from "../../hooks/useAgents";
import { PluginBadges, PluginDetailSection } from "../AgentControls/PluginBadges";
import { orgApiPath } from "../../stores/orgStore";
import { AgentModelOverrides } from "./AgentModelOverrides";

interface DelegationConfig {
  can_delegate_to: string[];
  accepts_from: string[];
}

export function AgentsTab() {
  const { data: agents = [] } = useAgents();
  const advisors = agents.filter((a) => a.type !== "external");
  const [expanded, setExpanded] = useState<string | null>(null);

  return (
    <div className="space-y-4">
      <h4 className="text-sm font-semibold">Agent Permissions & Delegation</h4>
      <div className="space-y-1">
        {advisors.map((agent) => (
          <AgentRow
            key={agent.id}
            agent={agent}
            allAgents={advisors}
            expanded={expanded === agent.id}
            onToggle={() => setExpanded(expanded === agent.id ? null : agent.id)}
            onUpdate={async () => {}}
          />
        ))}
      </div>
    </div>
  );
}

function AgentRow({
  agent,
  allAgents,
  expanded,
  onToggle,
  onUpdate,
}: {
  agent: AgentInfo;
  allAgents: AgentInfo[];
  expanded: boolean;
  onToggle: () => void;
  onUpdate: () => Promise<void>;
}) {
  const { mutateAsync: updatePersona } = useUpdatePersona();
  const [delegation, setDelegation] = useState<DelegationConfig | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!expanded) return;
    fetch(orgApiPath(`agents/${agent.id}/delegation`))
      .then((r) => r.ok ? r.json() : null)
      .then(setDelegation)
      .catch(() => {});
  }, [expanded, agent.id]);

  const saveDelegation = async () => {
    if (!delegation) return;
    setSaving(true);
    await fetch(orgApiPath(`agents/${agent.id}/delegation`), {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(delegation),
    });
    setSaving(false);
  };

  const toggleComms = async () => {
    await updatePersona({ agentId: agent.id, update: { comms_enabled: !agent.comms_enabled } });
  };

  return (
    <div className="border border-neutral/30 rounded bg-base-100">
      <button
        onClick={onToggle}
        className="w-full flex items-center justify-between px-3 py-2 text-left hover:bg-base-200/50 transition-colors"
      >
        <div className="flex items-center gap-2 min-w-0">
          <span className="w-2 h-2 rounded-full shrink-0" style={{ backgroundColor: agent.ui?.color }} />
          <span className="text-sm font-medium truncate">{agent.name}{agent.title_tag && <span className="font-normal text-base-content/50 ml-1">({agent.title_tag})</span>}</span>
          <span className="text-xs text-base-content/50">{agent.model}</span>
          <PluginBadges agent={agent} size="compact" />
        </div>
        <div className="flex items-center gap-2">
          {agent.comms_enabled && (
            <span className="badge badge-xs badge-outline">comms</span>
          )}
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth={2}
            className={`w-4 h-4 transition-transform ${expanded ? "rotate-180" : ""}`}
          >
            <path d="M6 9l6 6 6-6" />
          </svg>
        </div>
      </button>

      {expanded && (
        <div className="px-3 pb-3 pt-1 border-t border-neutral/20 space-y-3">
          <CommsRow
            agent={agent}
            enabled={agent.comms_enabled ?? false}
            onToggle={toggleComms}
          />

          {delegation ? (
            <DelegationEditor
              delegation={delegation}
              allAgents={allAgents}
              currentId={agent.id}
              onChange={setDelegation}
            />
          ) : (
            <div className="flex items-center gap-2 py-1">
              <span className="loading loading-spinner loading-xs" />
              <span className="text-xs text-base-content/60">Loading delegation...</span>
            </div>
          )}

          <PluginDetailSection agent={agent} />

          <AgentModelOverrides agentId={agent.id} />

          <button onClick={saveDelegation} disabled={saving || !delegation} className="btn btn-primary btn-xs">
            {saving ? <span className="loading loading-spinner loading-xs" /> : "Save Delegation"}
          </button>
        </div>
      )}
    </div>
  );
}

function CommsRow({ agent, enabled, onToggle }: { agent: AgentInfo; enabled: boolean; onToggle: () => void }) {
  return (
    <label className="flex items-center justify-between gap-3 cursor-pointer">
      <div>
        <span className="text-xs font-medium">Communications</span>
        {agent.email && (
          <p className="text-xs text-base-content/60 font-mono">{agent.email}</p>
        )}
      </div>
      <input
        type="checkbox"
        className="toggle toggle-xs toggle-primary"
        checked={enabled}
        onChange={onToggle}
      />
    </label>
  );
}

function DelegationEditor({
  delegation,
  allAgents,
  currentId,
  onChange,
}: {
  delegation: DelegationConfig;
  allAgents: AgentInfo[];
  currentId: string;
  onChange: (d: DelegationConfig) => void;
}) {
  const others = allAgents.filter((a) => a.id !== currentId);

  const toggleDelegate = (id: string) => {
    const list = delegation.can_delegate_to.includes(id)
      ? delegation.can_delegate_to.filter((x) => x !== id)
      : [...delegation.can_delegate_to, id];
    onChange({ ...delegation, can_delegate_to: list });
  };

  const toggleAccept = (id: string) => {
    const list = delegation.accepts_from.includes(id)
      ? delegation.accepts_from.filter((x) => x !== id)
      : [...delegation.accepts_from, id];
    onChange({ ...delegation, accepts_from: list });
  };

  return (
    <div className="space-y-2">
      <div>
        <span className="text-xs font-medium">Can delegate to</span>
        <div className="flex flex-wrap gap-1 mt-1">
          {others.map((a) => (
            <button
              key={a.id}
              onClick={() => toggleDelegate(a.id)}
              className={`badge badge-sm cursor-pointer ${
                delegation.can_delegate_to.includes(a.id) ? "badge-primary" : "badge-outline"
              }`}
            >
              {a.name}
            </button>
          ))}
        </div>
      </div>
      <div>
        <span className="text-xs font-medium">Accepts work from</span>
        <div className="flex flex-wrap gap-1 mt-1">
          {others.map((a) => (
            <button
              key={a.id}
              onClick={() => toggleAccept(a.id)}
              className={`badge badge-sm cursor-pointer ${
                delegation.accepts_from.includes(a.id) ? "badge-primary" : "badge-outline"
              }`}
            >
              {a.name}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

