import { useEffect, useState } from "react";
import { useOrgStore } from "../../stores/orgStore";
import { useOrgs, useUpdateOrg } from "../../hooks/useOrgs";
import { DiscordSection, type ChannelMapping } from "./DiscordSection";
import { SlackSection, type SlackChannelMapping } from "./SlackSection";
import { TeamsSection, type TeamsChannelMapping } from "./TeamsSection";
import { ZoomSection, type ZoomChannelMapping } from "./ZoomSection";
import { ToggleRow } from "./ToggleRow";

const ORG_TYPES = [
  { value: "startup", label: "Startup" },
  { value: "family", label: "Family" },
  { value: "job-hunt", label: "Job Hunt" },
  { value: "creator", label: "Creator" },
  { value: "student", label: "Student" },
  { value: "custom", label: "Custom" },
] as const;

type MappingEntry = { channelId: string; target: string };

function parseMappings(obj: Record<string, string> | undefined): MappingEntry[] {
  return Object.entries(obj || {}).map(([channelId, target]) => ({ channelId, target }));
}

function serializeMappings(entries: MappingEntry[]): Record<string, string> {
  const obj: Record<string, string> = {};
  for (const m of entries) {
    if (m.channelId.trim() && m.target) obj[m.channelId.trim()] = m.target;
  }
  return obj;
}

export function OrganizationTab() {
  const activeOrgId = useOrgStore((s) => s.activeOrgId);
  const { data: orgs = [] } = useOrgs();
  const updateOrgMutation = useUpdateOrg();
  const org = orgs.find((o) => o.id === activeOrgId);
  const [saving, setSaving] = useState(false);

  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [type, setType] = useState("");
  const [requireApproval, setRequireApproval] = useState(true);
  const [emailDomain, setEmailDomain] = useState("");
  const [emailSignature, setEmailSignature] = useState("");
  const [inboundPolling, setInboundPolling] = useState(false);
  const [guildId, setGuildId] = useState("");
  const [discordMappings, setDiscordMappings] = useState<ChannelMapping[]>([]);
  const [slackMappings, setSlackMappings] = useState<SlackChannelMapping[]>([]);
  const [tenantId, setTenantId] = useState("");
  const [teamsMappings, setTeamsMappings] = useState<TeamsChannelMapping[]>([]);
  const [zoomMappings, setZoomMappings] = useState<ZoomChannelMapping[]>([]);

  useEffect(() => {
    if (!org) return;
    setName(org.name);
    setDescription(org.description);
    setType(org.type);
    setRequireApproval(org.comms.require_approval);
    setEmailDomain(org.comms.email_domain);
    setEmailSignature(org.comms.email_signature);
    setInboundPolling(org.comms.inbound_polling);
    setGuildId(org.comms.discord?.guild_id || "");
    setDiscordMappings(parseMappings(org.comms.discord?.channel_mappings));
    setSlackMappings(parseMappings(org.comms.slack?.channel_mappings));
    setTenantId(org.comms.teams?.tenant_id || "");
    setTeamsMappings(parseMappings(org.comms.teams?.channel_mappings));
    setZoomMappings(parseMappings(org.comms.zoom?.channel_mappings));
  }, [org]);

  if (!org) return <p className="text-sm text-base-content/60">No organization selected.</p>;

  const agents = org.agents || [];
  const defaultTarget = agents[0]?.id || "huddle";
  const addEntry = (set: typeof setDiscordMappings, prev: MappingEntry[]) =>
    set([...prev, { channelId: "", target: defaultTarget }]);
  const updateEntry = (set: typeof setDiscordMappings, prev: MappingEntry[], idx: number, field: string, value: string) =>
    set(prev.map((m, i) => (i === idx ? { ...m, [field]: value } : m)));
  const removeEntry = (set: typeof setDiscordMappings, prev: MappingEntry[], idx: number) =>
    set(prev.filter((_, i) => i !== idx));

  const handleSave = async () => {
    setSaving(true);
    await updateOrgMutation.mutateAsync({
      orgId: org.id,
      update: {
        name, description, type,
        comms: {
          require_approval: requireApproval,
          email_domain: emailDomain,
          email_signature: emailSignature,
          inbound_polling: inboundPolling,
          discord: { guild_id: guildId, channel_mappings: serializeMappings(discordMappings) },
          slack: { channel_mappings: serializeMappings(slackMappings) },
          teams: { tenant_id: tenantId, channel_mappings: serializeMappings(teamsMappings) },
          zoom: { channel_mappings: serializeMappings(zoomMappings) },
        },
      },
    });
    setSaving(false);
  };

  return (
    <div className="space-y-6">
      <div className="space-y-3">
        <h4 className="text-sm font-semibold">Organization Details</h4>
        <label className="form-control">
          <span className="label-text text-xs mb-1">Name</span>
          <input type="text" value={name} onChange={(e) => setName(e.target.value)}
            className="input input-sm input-bordered w-full" />
        </label>
        <label className="form-control">
          <span className="label-text text-xs mb-1">Description</span>
          <textarea value={description} onChange={(e) => setDescription(e.target.value)}
            rows={2} className="textarea textarea-sm textarea-bordered w-full resize-y" />
        </label>
        <label className="form-control">
          <span className="label-text text-xs mb-1">Type</span>
          <select value={type} onChange={(e) => setType(e.target.value)}
            className="select select-sm select-bordered w-full">
            {ORG_TYPES.map((t) => (
              <option key={t.value} value={t.value}>{t.label}</option>
            ))}
          </select>
        </label>
      </div>

      <div className="divider my-0" />

      <div className="space-y-3">
        <h4 className="text-sm font-semibold">Communications</h4>
        <ToggleRow label="Require approval"
          description="Outbound messages need manual approval before sending"
          checked={requireApproval} onChange={setRequireApproval} />
        <ToggleRow label="Inbound polling"
          description="Automatically check for incoming emails"
          checked={inboundPolling} onChange={setInboundPolling} />
        <label className="form-control">
          <span className="label-text text-xs mb-1">Email domain</span>
          <input type="text" value={emailDomain} onChange={(e) => setEmailDomain(e.target.value)}
            placeholder="e.g. axon.yourcompany.com" className="input input-sm input-bordered w-full font-mono" />
        </label>
        <label className="form-control">
          <span className="label-text text-xs mb-1">Email signature</span>
          <textarea value={emailSignature} onChange={(e) => setEmailSignature(e.target.value)}
            rows={3} placeholder="HTML or plain text appended to outbound emails"
            className="textarea textarea-sm textarea-bordered w-full resize-y font-mono text-xs" />
        </label>
      </div>

      <div className="divider my-0" />

      <DiscordSection guildId={guildId} onGuildIdChange={setGuildId}
        mappings={discordMappings} agents={agents} hasHuddle={org.has_huddle}
        onAddMapping={() => addEntry(setDiscordMappings, discordMappings)}
        onUpdateMapping={(i, f, v) => updateEntry(setDiscordMappings, discordMappings, i, f, v)}
        onRemoveMapping={(i) => removeEntry(setDiscordMappings, discordMappings, i)} />

      <div className="divider my-0" />

      <SlackSection mappings={slackMappings} agents={agents} hasHuddle={org.has_huddle}
        onAddMapping={() => addEntry(setSlackMappings, slackMappings)}
        onUpdateMapping={(i, f, v) => updateEntry(setSlackMappings, slackMappings, i, f, v)}
        onRemoveMapping={(i) => removeEntry(setSlackMappings, slackMappings, i)} />

      <div className="divider my-0" />

      <TeamsSection tenantId={tenantId} onTenantIdChange={setTenantId}
        mappings={teamsMappings} agents={agents} hasHuddle={org.has_huddle}
        onAddMapping={() => addEntry(setTeamsMappings, teamsMappings)}
        onUpdateMapping={(i, f, v) => updateEntry(setTeamsMappings, teamsMappings, i, f, v)}
        onRemoveMapping={(i) => removeEntry(setTeamsMappings, teamsMappings, i)} />

      <div className="divider my-0" />

      <ZoomSection mappings={zoomMappings} agents={agents} hasHuddle={org.has_huddle}
        onAddMapping={() => addEntry(setZoomMappings, zoomMappings)}
        onUpdateMapping={(i, f, v) => updateEntry(setZoomMappings, zoomMappings, i, f, v)}
        onRemoveMapping={(i) => removeEntry(setZoomMappings, zoomMappings, i)} />

      <button onClick={handleSave} disabled={saving} className="btn btn-primary btn-sm">
        {saving ? <span className="loading loading-spinner loading-xs" /> : "Save Changes"}
      </button>
    </div>
  );
}
