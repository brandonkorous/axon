import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useCreateSkill } from "../../hooks/useSkills";
import { TagInput } from "../Plugins/TagInput";

const CATEGORIES = ["general", "research", "analysis", "engineering", "communication", "planning"];

function Hint({ children }: { children: React.ReactNode }) {
  return <p className="text-xs text-base-content/50 mt-1">{children}</p>;
}

export function SkillCreateView() {
  const navigate = useNavigate();
  const createSkill = useCreateSkill();

  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [version, setVersion] = useState("1.0.0");
  const [author, setAuthor] = useState("axon");
  const [category, setCategory] = useState("general");
  const [icon, setIcon] = useState("");
  const [autoInject, setAutoInject] = useState(false);
  const [triggers, setTriggers] = useState<string[]>([]);
  const [methodology, setMethodology] = useState("");
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState("");

  const nameValid = /^[a-z][a-z0-9_]*$/.test(name);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim() || !nameValid) return;

    setCreating(true);
    setError("");

    try {
      await createSkill.mutateAsync({
        name, description, version, author, category, icon,
        auto_inject: autoInject, triggers, methodology,
      } as any);
      navigate("/skills");
    } catch {
      setError("Failed to create skill. Name may already be taken.");
      setCreating(false);
    }
  };

  return (
    <div className="h-full flex flex-col">
      <div className="px-6 py-4 border-b border-neutral">
        <button onClick={() => navigate("/skills")} className="btn btn-ghost btn-xs mb-2">
          &larr; Back to Skills
        </button>
        <h1 className="text-xl font-bold text-base-content">New Skill</h1>
        <p className="text-xs text-base-content/60 mt-1">
          Skills are cognitive reasoning patterns that inject methodology into agent prompts.
          Define the thinking process an agent should follow for specific types of work.
        </p>
      </div>

      <div className="flex-1 overflow-y-auto p-6">
        <form onSubmit={handleSubmit} className="max-w-xl mx-auto space-y-6">
          {error && <div className="alert alert-error text-sm">{error}</div>}

          {/* -- Identity -- */}
          <fieldset className="space-y-4">
            <legend className="text-sm font-semibold text-base-content/80">Identity</legend>

            <label className="form-control">
              <span className="label-text text-xs mb-1">Name *</span>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value.toLowerCase().replace(/[^a-z0-9_]/g, ""))}
                placeholder="deep_research"
                className={`input input-sm input-bordered w-full ${name && !nameValid ? "input-error" : ""}`}
              />
              {name && !nameValid ? (
                <span className="text-xs text-error mt-1">Must start with a letter and contain only lowercase letters, digits, and underscores</span>
              ) : (
                <Hint>Unique identifier for this skill. Cannot be changed after creation.</Hint>
              )}
            </label>

            <label className="form-control">
              <span className="label-text text-xs mb-1">Description</span>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Systematic deep research methodology with source validation"
                rows={3}
                className="textarea textarea-sm textarea-bordered w-full resize-y"
              />
              <Hint>Explain what reasoning pattern this skill provides and when agents should use it.</Hint>
            </label>

            <div className="grid grid-cols-2 gap-3">
              <label className="form-control">
                <span className="label-text text-xs mb-1">Version</span>
                <input type="text" value={version} onChange={(e) => setVersion(e.target.value)} className="input input-sm input-bordered w-full" />
              </label>
              <label className="form-control">
                <span className="label-text text-xs mb-1">Author</span>
                <input type="text" value={author} onChange={(e) => setAuthor(e.target.value)} className="input input-sm input-bordered w-full" />
              </label>
            </div>
          </fieldset>

          <div className="divider my-0" />

          {/* -- Appearance -- */}
          <fieldset className="space-y-4">
            <legend className="text-sm font-semibold text-base-content/80">Appearance</legend>
            <div className="grid grid-cols-2 gap-3">
              <label className="form-control">
                <span className="label-text text-xs mb-1">Category</span>
                <select value={category} onChange={(e) => setCategory(e.target.value)} className="select select-sm select-bordered w-full">
                  {CATEGORIES.map((c) => (<option key={c} value={c}>{c}</option>))}
                </select>
                <Hint>Groups the skill in the browser.</Hint>
              </label>
              <label className="form-control">
                <span className="label-text text-xs mb-1">Icon</span>
                <input type="text" value={icon} onChange={(e) => setIcon(e.target.value)} placeholder="microscope" className="input input-sm input-bordered w-full" />
                <Hint>Icon name or emoji shown in the UI.</Hint>
              </label>
            </div>
          </fieldset>

          <div className="divider my-0" />

          {/* -- Activation -- */}
          <fieldset className="space-y-4">
            <legend className="text-sm font-semibold text-base-content/80">Activation</legend>

            <label className="flex items-center gap-3 cursor-pointer">
              <input type="checkbox" className="toggle toggle-sm toggle-primary" checked={autoInject} onChange={(e) => setAutoInject(e.target.checked)} />
              <div>
                <span className="text-sm">Auto-inject</span>
                <Hint>When enabled, this skill's methodology is always included in the agent's prompt. When off, the skill only activates when a trigger keyword is detected.</Hint>
              </div>
            </label>

            <label className="form-control">
              <span className="label-text text-xs mb-1">Trigger Keywords</span>
              <TagInput tags={triggers} onChange={setTriggers} placeholder="Add keyword and press Enter" />
              <Hint>Words or phrases that cause this skill to activate. When detected in a message, the methodology is injected into the agent's prompt for that turn.</Hint>
            </label>
          </fieldset>

          <div className="divider my-0" />

          {/* -- Methodology -- */}
          <fieldset className="space-y-4">
            <legend className="text-sm font-semibold text-base-content/80">Methodology</legend>

            <label className="form-control">
              <span className="label-text text-xs mb-1">Methodology Content</span>
              <textarea
                value={methodology}
                onChange={(e) => setMethodology(e.target.value)}
                placeholder={"# Deep Research Methodology\n\n## Step 1: Define the question\n..."}
                rows={12}
                className="textarea textarea-sm textarea-bordered w-full resize-y font-mono text-sm"
              />
              <Hint>Write the reasoning pattern in Markdown. This content is injected verbatim into the agent's system prompt when the skill activates. Describe the step-by-step thinking process the agent should follow.</Hint>
            </label>
          </fieldset>

          <div className="divider my-0" />

          {/* What happens next */}
          <div className="rounded-lg bg-base-300 border border-neutral p-4 space-y-2">
            <h3 className="text-sm font-semibold text-base-content/80">What happens next?</h3>
            <p className="text-xs text-base-content/60 leading-relaxed">
              Creating a skill registers a cognitive pattern that can be enabled for any agent.
              When activated, the methodology is injected into the agent's prompt, guiding its
              reasoning process. You can enable it for specific agents from the skill detail page.
            </p>
          </div>

          <button type="submit" disabled={!name.trim() || !nameValid || creating} className="btn btn-primary btn-sm w-full">
            {creating ? <span className="loading loading-spinner loading-xs" /> : "Create Skill"}
          </button>
        </form>
      </div>
    </div>
  );
}
