import { SetupSteps } from "./SetupSteps";

interface ChannelMapping {
  channelId: string;
  target: string;
}

interface SlackSectionProps {
  mappings: ChannelMapping[];
  agents: { id: string; name: string; title: string }[];
  hasHuddle: boolean;
  onAddMapping: () => void;
  onUpdateMapping: (idx: number, field: keyof ChannelMapping, value: string) => void;
  onRemoveMapping: (idx: number) => void;
}

export type { ChannelMapping as SlackChannelMapping };

const SLACK_STEPS = [
  <>Go to <strong>api.slack.com/apps</strong> → <strong>Create New App</strong> → choose <strong>From scratch</strong>.</>,
  <>Enable <strong>Socket Mode</strong> (Settings → Socket Mode → toggle on). Generate an App-Level Token with the <code>connections:write</code> scope. This is your <code>slack_app_token</code> (starts with <code>xapp-</code>).</>,
  <>Go to <strong>OAuth &amp; Permissions</strong> and add Bot Token Scopes: <code>chat:write</code>, <code>channels:read</code>, <code>channels:history</code>, <code>groups:read</code>, <code>groups:history</code>.</>,
  <>Click <strong>Install to Workspace</strong> and authorize. Copy the <strong>Bot User OAuth Token</strong> — this is your <code>slack_bot_token</code> (starts with <code>xoxb-</code>).</>,
  <>Go to <strong>Event Subscriptions</strong> → enable events. Subscribe to bot events: <code>message.channels</code> and <code>message.groups</code>.</>,
  <>Invite the bot to channels by typing <code>/invite @YourBotName</code> in each channel.</>,
  <>To find Channel IDs: right-click a channel → <strong>View channel details</strong> → copy the ID from the bottom of the modal.</>,
];

const SLACK_CAPABILITIES = [
  "Receive and respond to messages in mapped channels (via Socket Mode)",
  "Send outbound messages (with optional approval)",
];

export function SlackSection({
  mappings, agents, hasHuddle, onAddMapping, onUpdateMapping, onRemoveMapping,
}: SlackSectionProps) {
  return (
    <div className="space-y-3">
      <h4 className="text-sm font-semibold">Slack</h4>
      <SetupSteps
        credentials={[
          { key: "slack_bot_token", label: "Bot User OAuth Token (xoxb-...)" },
          { key: "slack_app_token", label: "App-Level Token (xapp-...)" },
        ]}
        steps={SLACK_STEPS}
        capabilities={SLACK_CAPABILITIES}
        note="No public URL required — uses Socket Mode (WebSocket connection)."
      />

      <div>
        <span className="label-text text-xs">Channel Mappings</span>
        <p className="text-xs text-base-content/60 mt-0.5 mb-2">
          Route Slack channels to specific agents or the huddle.
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
