import { SetupSteps } from "./SetupSteps";

interface ChannelMapping {
  channelId: string;
  target: string;
}

interface TeamsSectionProps {
  tenantId: string;
  onTenantIdChange: (v: string) => void;
  mappings: ChannelMapping[];
  agents: { id: string; name: string; title: string }[];
  hasHuddle: boolean;
  onAddMapping: () => void;
  onUpdateMapping: (idx: number, field: keyof ChannelMapping, value: string) => void;
  onRemoveMapping: (idx: number) => void;
}

export type { ChannelMapping as TeamsChannelMapping };

const TEAMS_STEPS = [
  <>Go to the <strong>Azure Portal</strong> → search for <strong>Azure Bot</strong> → <strong>Create</strong>. Choose <strong>Multi Tenant</strong> for the bot type.</>,
  <>After creation, go to <strong>Configuration</strong>. Copy the <strong>Microsoft App ID</strong> — add it as a <code>teams_app_id</code> credential.</>,
  <>Click <strong>Manage Password</strong> → <strong>New client secret</strong>. Copy the value — add it as a <code>teams_app_secret</code> credential.</>,
  <>Set the <strong>Messaging endpoint</strong> to <code>{"https://<your-host>/api/teams/messages"}</code>.</>,
  <>Go to <strong>Channels</strong> → add the <strong>Microsoft Teams</strong> channel.</>,
  <>For meeting creation: go to <strong>Azure AD → Users</strong>, find the meeting organizer, copy their <strong>Object ID</strong> — add it as a <code>teams_organizer_id</code> credential.</>,
  <>In <strong>Azure AD → App Registrations</strong>, find your bot app. Go to <strong>API Permissions</strong> → add <code>OnlineMeetings.ReadWrite.All</code> (Application) and grant admin consent.</>,
  <>Copy your <strong>Tenant ID</strong> from Azure AD → Overview and paste it below.</>,
];

const TEAMS_CAPABILITIES = [
  "Receive and respond to messages in mapped channels",
  "Send outbound messages (with optional approval)",
  "Create online meetings with join URLs",
];

export function TeamsSection({
  tenantId, onTenantIdChange, mappings, agents, hasHuddle,
  onAddMapping, onUpdateMapping, onRemoveMapping,
}: TeamsSectionProps) {
  return (
    <div className="space-y-3">
      <h4 className="text-sm font-semibold">Microsoft Teams</h4>
      <SetupSteps
        credentials={[
          { key: "teams_app_id", label: "Microsoft App ID" },
          { key: "teams_app_secret", label: "Client secret" },
          { key: "teams_organizer_id", label: "Organizer Object ID (for meetings)" },
        ]}
        steps={TEAMS_STEPS}
        capabilities={TEAMS_CAPABILITIES}
        note="Requires a publicly accessible URL for the messaging endpoint."
      />

      <label className="form-control">
        <span className="label-text text-xs mb-1">Azure AD Tenant ID</span>
        <input type="text" value={tenantId} onChange={(e) => onTenantIdChange(e.target.value)}
          placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
          className="input input-sm input-bordered w-full font-mono" />
      </label>

      <div>
        <span className="label-text text-xs">Channel Mappings</span>
        <p className="text-xs text-base-content/60 mt-0.5 mb-2">
          Route Teams channels to specific agents or the huddle.
        </p>
        <div className="space-y-2">
          {mappings.map((m, idx) => (
            <div key={idx} className="flex items-center gap-2">
              <input type="text" value={m.channelId}
                onChange={(e) => onUpdateMapping(idx, "channelId", e.target.value)}
                placeholder="Channel ID" className="input input-sm input-bordered flex-1 font-mono" />
              <select value={m.target} onChange={(e) => onUpdateMapping(idx, "target", e.target.value)}
                className="select select-sm select-bordered flex-1">
                {agents.map((a) => (
                  <option key={a.id} value={a.id}>{a.name}{a.title ? ` — ${a.title}` : ""}</option>
                ))}
                {hasHuddle && <option value="huddle">Huddle (all advisors)</option>}
              </select>
              <button type="button" onClick={() => onRemoveMapping(idx)}
                className="btn btn-ghost btn-sm btn-square text-error" aria-label="Remove mapping">&times;</button>
            </div>
          ))}
        </div>
        <button type="button" onClick={onAddMapping}
          className="btn btn-ghost btn-xs mt-2 text-base-content/60">+ Add channel</button>
      </div>
    </div>
  );
}
