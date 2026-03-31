import { useState } from "react";
import { useAgentStore } from "../../stores/agentStore";
import { useOrgStore } from "../../stores/orgStore";
import { ChannelMappings } from "./ChannelMappings";

export function CommsSection({ agentId }: { agentId: string }) {
  const { agents, updatePersona } = useAgentStore();
  const agent = agents.find((a) => a.id === agentId);
  const org = useOrgStore((s) => s.orgs.find((o) => o.id === s.activeOrgId));
  const comms = org?.comms;

  const [commsEnabled, setCommsEnabled] = useState(agent?.comms_enabled ?? false);
  const [emailAlias, setEmailAlias] = useState(agent?.email_alias ?? "");
  const [actionBias, setActionBias] = useState<"proactive" | "balanced" | "deliberative">(agent?.action_bias ?? "proactive");
  const [saving, setSaving] = useState(false);
  const [dirty, setDirty] = useState(false);

  const emailDomain = agent?.email?.includes("@")
    ? agent.email.split("@")[1]
    : comms?.email_domain || null;

  if (!agent) return null;

  // Find Discord channels mapped to this agent
  const discordChannels = comms?.discord?.channel_mappings
    ? Object.entries(comms.discord.channel_mappings)
        .filter(([, mapped]) => mapped === agentId)
        .map(([channelId]) => channelId)
    : [];

  // Find Slack channels mapped to this agent
  const slackChannels = comms?.slack?.channel_mappings
    ? Object.entries(comms.slack.channel_mappings)
        .filter(([, mapped]) => mapped === agentId)
        .map(([channelId]) => channelId)
    : [];

  const hasDiscord = !!comms?.discord?.guild_id;
  const hasSlack = !!comms?.slack?.channel_mappings && Object.keys(comms.slack.channel_mappings).length > 0;

  const handleSave = async () => {
    setSaving(true);
    try {
      await updatePersona(agentId, {
        comms_enabled: commsEnabled,
        email_alias: emailAlias,
        action_bias: actionBias,
      });
      setDirty(false);
    } finally {
      setSaving(false);
    }
  };

  const mark = <T,>(setter: (v: T) => void) => (v: T) => {
    setter(v);
    setDirty(true);
  };

  return (
    <div className="space-y-4">
      {/* Comms toggle */}
      <label className="flex items-center justify-between cursor-pointer">
        <div>
          <span className="text-xs font-medium">Comms enabled</span>
          <p className="text-[11px] text-base-content/50">Email &amp; messaging</p>
        </div>
        <input
          type="checkbox"
          checked={commsEnabled}
          onChange={(e) => mark(setCommsEnabled)(e.target.checked)}
          className="toggle toggle-sm toggle-primary"
        />
      </label>

      {/* Email */}
      {(commsEnabled || agent.email) && emailDomain && (
        <div>
          <span className="text-xs font-medium block mb-1">Email address</span>
          <div className="flex items-center gap-0">
            <input
              type="text"
              value={emailAlias}
              onChange={(e) =>
                mark(setEmailAlias)(
                  e.target.value.toLowerCase().replace(/[^a-z0-9._-]/g, "")
                )
              }
              placeholder={agent.id}
              className="input input-sm input-bordered rounded-r-none w-full font-mono"
            />
            <span className="bg-base-100 border border-l-0 border-neutral/30 rounded-r-lg px-3 py-1.5 text-xs text-base-content/60 font-mono whitespace-nowrap">
              @{emailDomain}
            </span>
          </div>
          <p className="text-[11px] text-base-content/50 mt-1">
            Leave empty to use default ({agent.id})
          </p>
        </div>
      )}

      {/* Discord */}
      {hasDiscord && (
        <ChannelMappings
          agentId={agentId}
          platform="discord"
          channels={discordChannels}
          allMappings={comms?.discord?.channel_mappings ?? {}}
        />
      )}

      {/* Slack */}
      {hasSlack && (
        <ChannelMappings
          agentId={agentId}
          platform="slack"
          channels={slackChannels}
          allMappings={comms?.slack?.channel_mappings ?? {}}
        />
      )}

      {/* Action bias */}
      <div>
        <span className="text-xs font-medium block mb-1">Action Bias</span>
        <select
          value={actionBias}
          onChange={(e) => mark(setActionBias)(e.target.value as "proactive" | "balanced" | "deliberative")}
          className="select select-sm select-bordered w-full"
        >
          <option value="proactive">Proactive — Act first, explain after</option>
          <option value="balanced">Balanced — Act on clear, clarify ambiguous</option>
          <option value="deliberative">Deliberative — Think before high-stakes</option>
        </select>
      </div>

      {/* Save */}
      {dirty && (
        <button
          onClick={handleSave}
          disabled={saving}
          className="btn btn-primary btn-xs"
        >
          {saving ? (
            <span className="loading loading-spinner loading-xs" />
          ) : (
            "Save"
          )}
        </button>
      )}
    </div>
  );
}
