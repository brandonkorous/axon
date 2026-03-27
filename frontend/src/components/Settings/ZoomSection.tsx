import { SetupSteps } from "./SetupSteps";

interface ChannelMapping {
  channelId: string;
  target: string;
}

interface ZoomSectionProps {
  mappings: ChannelMapping[];
  agents: { id: string; name: string; title: string }[];
  hasHuddle: boolean;
  onAddMapping: () => void;
  onUpdateMapping: (idx: number, field: keyof ChannelMapping, value: string) => void;
  onRemoveMapping: (idx: number) => void;
}

export type { ChannelMapping as ZoomChannelMapping };

const ZOOM_STEPS = [
  <>Go to the <strong>Zoom App Marketplace</strong> → <strong>Develop</strong> → <strong>Build App</strong>. Choose <strong>Server-to-Server OAuth</strong>.</>,
  <>Copy the <strong>Account ID</strong>, <strong>Client ID</strong>, and <strong>Client Secret</strong> from the app credentials page. Add each as credentials in Axon.</>,
  <>Go to <strong>Scopes</strong> and add: <code>meeting:write:admin</code> (create meetings), <code>chat_message:write</code> (send Team Chat), <code>chat_channel:read</code> (read channels).</>,
  <>For inbound Team Chat: go to <strong>Feature → Event Subscriptions</strong>. Set the Event notification endpoint URL to <code>{"https://<your-host>/api/zoom/events"}</code>.</>,
  <>Subscribe to the event: <code>chat_message.sent</code>.</>,
  <><strong>Activate</strong> the app. Zoom will validate the webhook endpoint during activation.</>,
  <>To find Team Chat Channel IDs: use the Zoom API or check channel details in Zoom Team Chat.</>,
];

const ZOOM_CAPABILITIES = [
  "Receive and respond to Team Chat messages in mapped channels",
  "Send outbound Team Chat messages (with optional approval)",
  "Create instant or scheduled meetings with join URLs",
];

export function ZoomSection({
  mappings, agents, hasHuddle, onAddMapping, onUpdateMapping, onRemoveMapping,
}: ZoomSectionProps) {
  return (
    <div className="space-y-3">
      <h4 className="text-sm font-semibold">Zoom</h4>
      <SetupSteps
        credentials={[
          { key: "zoom_account_id", label: "Account ID" },
          { key: "zoom_client_id", label: "Client ID" },
          { key: "zoom_client_secret", label: "Client Secret" },
        ]}
        steps={ZOOM_STEPS}
        capabilities={ZOOM_CAPABILITIES}
        note="Webhook endpoint requires a publicly accessible URL. Meeting creation works without webhooks."
      />

      <div>
        <span className="label-text text-xs">Team Chat Channel Mappings</span>
        <p className="text-xs text-base-content/60 mt-0.5 mb-2">
          Route Zoom Team Chat channels to specific agents or the huddle.
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
