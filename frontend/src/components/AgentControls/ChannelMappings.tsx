import { useState } from "react";
import { useOrgStore } from "../../stores/orgStore";

type Platform = "discord" | "slack";

export function ChannelMappings({
  agentId,
  platform,
  channels,
  allMappings,
}: {
  agentId: string;
  platform: Platform;
  channels: string[];
  allMappings: Record<string, string>;
}) {
  const { activeOrgId } = useOrgStore();
  const updateOrg = useOrgStore((s) => s.updateOrg);
  const [newChannel, setNewChannel] = useState("");
  const [saving, setSaving] = useState(false);

  const label = platform === "discord" ? "Discord" : "Slack";

  const assign = async () => {
    const id = newChannel.trim();
    if (!id) return;
    setSaving(true);
    const updated = { ...allMappings, [id]: agentId };
    await updateOrg(activeOrgId, { comms: { [platform]: { channel_mappings: updated } } });
    setNewChannel("");
    setSaving(false);
  };

  const unassign = async (channelId: string) => {
    setSaving(true);
    const updated = { ...allMappings };
    delete updated[channelId];
    await updateOrg(activeOrgId, { comms: { [platform]: { channel_mappings: updated } } });
    setSaving(false);
  };

  return (
    <div>
      <span className="text-xs font-medium block mb-1">{label}</span>

      {channels.length > 0 && (
        <div className="space-y-1 mb-2">
          {channels.map((id) => (
            <div key={id} className="flex items-center justify-between py-1">
              <div className="flex items-center gap-2 min-w-0">
                <span className="badge badge-xs badge-success">connected</span>
                <span className="text-xs font-mono text-base-content/70 truncate">{id}</span>
              </div>
              <button
                onClick={() => unassign(id)}
                disabled={saving}
                className="btn btn-ghost btn-xs text-error"
              >
                Remove
              </button>
            </div>
          ))}
        </div>
      )}

      <div className="flex items-center gap-1.5">
        <input
          type="text"
          value={newChannel}
          onChange={(e) => setNewChannel(e.target.value.trim())}
          placeholder="Channel ID"
          className="input input-sm input-bordered flex-1 font-mono"
          onKeyDown={(e) => e.key === "Enter" && assign()}
        />
        <button
          onClick={assign}
          disabled={saving || !newChannel.trim()}
          className="btn btn-soft btn-primary btn-sm"
        >
          {saving ? <span className="loading loading-spinner loading-xs" /> : "Assign"}
        </button>
      </div>
      <p className="text-[11px] text-base-content/50 mt-1">
        Paste a {label} channel ID to assign this agent
      </p>
    </div>
  );
}
