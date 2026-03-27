import { SetupSteps } from "./SetupSteps";

interface ChannelMapping {
  channelId: string;
  target: string;
}

interface DiscordSectionProps {
  guildId: string;
  onGuildIdChange: (v: string) => void;
  mappings: ChannelMapping[];
  agents: { id: string; name: string; title: string }[];
  hasHuddle: boolean;
  onAddMapping: () => void;
  onUpdateMapping: (idx: number, field: keyof ChannelMapping, value: string) => void;
  onRemoveMapping: (idx: number) => void;
}

export type { ChannelMapping };

const DISCORD_STEPS = [
  <>Go to the <strong>Discord Developer Portal</strong> and create a new Application.</>,
  <>Navigate to <strong>Bot</strong> → <strong>Add Bot</strong>. Copy the <strong>Bot Token</strong> and add it as a <code>discord</code> credential in Axon.</>,
  <>Under <strong>Privileged Gateway Intents</strong>, enable <strong>Message Content Intent</strong> and <strong>Server Members Intent</strong>.</>,
  <>Go to <strong>OAuth2 → URL Generator</strong>. Select scopes: <code>bot</code>. Select permissions: <code>Send Messages</code>, <code>Read Message History</code>, <code>Manage Events</code>, <code>View Channels</code>.</>,
  <>Open the generated URL to invite the bot to your server.</>,
  <>In Discord, enable <strong>Developer Mode</strong> (User Settings → Advanced). Right-click your server → <strong>Copy Server ID</strong> and paste it below.</>,
  <>Right-click channels → <strong>Copy Channel ID</strong> to set up channel mappings below.</>,
];

const DISCORD_CAPABILITIES = [
  "Receive and respond to messages in mapped channels",
  "Send outbound messages (with optional approval)",
  "Create scheduled events in the server",
];

export function DiscordSection({
  guildId, onGuildIdChange, mappings, agents, hasHuddle,
  onAddMapping, onUpdateMapping, onRemoveMapping,
}: DiscordSectionProps) {
  return (
    <div className="space-y-3">
      <h4 className="text-sm font-semibold">Discord</h4>
      <SetupSteps
        credentials={[{ key: "discord", label: "Bot token" }]}
        steps={DISCORD_STEPS}
        capabilities={DISCORD_CAPABILITIES}
        note="No public URL required — connects via Discord Gateway (WebSocket)."
      />

      <label className="form-control">
        <span className="label-text text-xs mb-1">Server (Guild) ID</span>
        <input type="text" value={guildId} onChange={(e) => onGuildIdChange(e.target.value)}
          placeholder="Right-click server → Copy Server ID"
          className="input input-sm input-bordered w-full font-mono" />
      </label>

      <div>
        <span className="label-text text-xs">Channel Mappings</span>
        <p className="text-xs text-base-content/60 mt-0.5 mb-2">
          Route Discord channels to specific agents or the huddle.
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
