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
  const [systemPrompt, setSystemPrompt] = useState("");

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
