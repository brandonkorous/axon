import { useEffect, useState } from "react";
import {
  AgentInfo,
  PersonaUpdate,
  useAgentStore,
} from "../../stores/agentStore";

export function PersonaEditor({
  agent,
  onClose,
}: {
  agent: AgentInfo;
  onClose: () => void;
}) {
  const { updatePersona, fetchAgentDetail } = useAgentStore();
  const [saving, setSaving] = useState(false);
  const [loaded, setLoaded] = useState(false);

  const [name, setName] = useState(agent.name);
  const [title, setTitle] = useState(agent.title);
  const [titleTag, setTitleTag] = useState(agent.title_tag ?? "");
  const [tagline, setTagline] = useState(agent.tagline);
  const [color, setColor] = useState(agent.ui.color);
  const [sparkleColor, setSparkleColor] = useState(agent.ui.sparkle_color);
  const [commsEnabled, setCommsEnabled] = useState(agent.comms_enabled ?? false);
  const [emailAlias, setEmailAlias] = useState(agent.email_alias ?? "");
  const [systemPrompt, setSystemPrompt] = useState("");

  // Derive the domain from the current email address
  const emailDomain = agent.email?.includes("@")
    ? agent.email.split("@")[1]
    : null;

  // Load full detail (including system_prompt) on mount
  useEffect(() => {
    if (loaded) return;
    fetchAgentDetail(agent.id).then((detail) => {
      if (detail?.system_prompt !== undefined) {
        setSystemPrompt(detail.system_prompt);
      }
      setLoaded(true);
    });
  }, [loaded, agent.id, fetchAgentDetail]);

  const handleSave = async () => {
    setSaving(true);
    const update: PersonaUpdate = {};
    if (name !== agent.name) update.name = name;
    if (title !== agent.title) update.title = title;
    if (titleTag !== (agent.title_tag ?? "")) update.title_tag = titleTag;
    if (tagline !== agent.tagline) update.tagline = tagline;
    if (color !== agent.ui.color) update.color = color;
    if (sparkleColor !== agent.ui.sparkle_color)
      update.sparkle_color = sparkleColor;
    if (systemPrompt) update.system_prompt = systemPrompt;
    if (commsEnabled !== (agent.comms_enabled ?? false))
      update.comms_enabled = commsEnabled;
    if (emailAlias !== (agent.email_alias ?? ""))
      update.email_alias = emailAlias;

    try {
      await updatePersona(agent.id, update);
      onClose();
    } catch {
      // keep open on error
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-3 border-t border-neutral pt-3">
      <div className="grid grid-cols-[1fr_1fr_5rem] gap-3">
        <label className="form-control">
          <span className="label-text text-xs mb-1">Name</span>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="input input-sm input-bordered w-full"
          />
        </label>
        <label className="form-control">
          <span className="label-text text-xs mb-1">Title</span>
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="e.g. Chief Executive Officer"
            className="input input-sm input-bordered w-full"
          />
        </label>
        <label className="form-control">
          <span className="label-text text-xs mb-1">Tag</span>
          <input
            type="text"
            value={titleTag}
            onChange={(e) => setTitleTag(e.target.value.toUpperCase().slice(0, 4))}
            placeholder="CTO"
            maxLength={4}
            className="input input-sm input-bordered w-full font-mono tracking-wide"
          />
        </label>
      </div>

      <label className="form-control">
        <span className="label-text text-xs mb-1">Tagline</span>
        <input
          type="text"
          value={tagline}
          onChange={(e) => setTagline(e.target.value)}
          placeholder="Short description of this agent's role"
          className="input input-sm input-bordered w-full"
        />
      </label>

      <div className="form-control">
        <label className="label cursor-pointer justify-start gap-3">
          <input
            type="checkbox"
            checked={commsEnabled}
            onChange={(e) => setCommsEnabled(e.target.checked)}
            className="toggle toggle-sm toggle-primary"
          />
          <span className="label-text text-xs">
            Comms enabled
            <span className="text-base-content/60 ml-1">(email &amp; Discord)</span>
          </span>
        </label>
      </div>

      {(commsEnabled || agent.email) && emailDomain && (
        <label className="form-control">
          <span className="label-text text-xs mb-1">Email address</span>
          <div className="flex items-center gap-0">
            <input
              type="text"
              value={emailAlias}
              onChange={(e) => setEmailAlias(e.target.value.toLowerCase().replace(/[^a-z0-9._-]/g, ""))}
              placeholder={agent.id}
              className="input input-sm input-bordered rounded-r-none w-full font-mono"
            />
            <span className="bg-base-100 border border-l-0 border-neutral/30 rounded-r-lg px-3 py-1.5 text-xs text-base-content/60 font-mono whitespace-nowrap">
              @{emailDomain}
            </span>
          </div>
          <div className="text-[11px] text-base-content/60 mt-1">
            Leave empty to use default ({agent.id})
          </div>
        </label>
      )}

      <div className="flex gap-3">
        <label className="form-control">
          <span className="label-text text-xs mb-1">Color</span>
          <div className="flex items-center gap-2">
            <input
              type="color"
              value={color}
              onChange={(e) => setColor(e.target.value)}
              className="w-8 h-8 rounded cursor-pointer border border-neutral"
            />
            <span className="text-xs text-base-content/60 font-mono">
              {color}
            </span>
          </div>
        </label>
        <label className="form-control">
          <span className="label-text text-xs mb-1">Sparkle</span>
          <div className="flex items-center gap-2">
            <input
              type="color"
              value={sparkleColor}
              onChange={(e) => setSparkleColor(e.target.value)}
              className="w-8 h-8 rounded cursor-pointer border border-neutral"
            />
            <span className="text-xs text-base-content/60 font-mono">
              {sparkleColor}
            </span>
          </div>
        </label>
      </div>

      <label className="form-control">
        <span className="label-text text-xs mb-1">System Prompt</span>
        {!loaded ? (
          <div className="flex items-center gap-2 py-2">
            <span className="loading loading-spinner loading-xs" />
            <span className="text-xs text-base-content/60">Loading...</span>
          </div>
        ) : (
          <textarea
            value={systemPrompt}
            onChange={(e) => setSystemPrompt(e.target.value)}
            placeholder="Instructions that define this agent's behavior, knowledge, and personality..."
            rows={8}
            className="textarea textarea-sm textarea-bordered w-full font-mono text-xs resize-y"
          />
        )}
      </label>

      <div className="flex gap-2">
        <button
          onClick={handleSave}
          disabled={saving || !name.trim()}
          className="btn btn-primary btn-xs"
        >
          {saving ? (
            <span className="loading loading-spinner loading-xs" />
          ) : (
            "Save Persona"
          )}
        </button>
        <button onClick={onClose} className="btn btn-ghost btn-xs">
          Cancel
        </button>
      </div>
    </div>
  );
}
