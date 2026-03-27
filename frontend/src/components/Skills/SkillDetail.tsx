import { useEffect, useState } from "react";
import { useSkillStore } from "../../stores/skillStore";
import { useAgentStore } from "../../stores/agentStore";
import { SkillEditForm } from "./SkillEditForm";

export function SkillDetail({ skillName, onBack }: { skillName: string; onBack: () => void }) {
  const { selectedSkill, fetchSkillDetail, enableSkill, disableSkill, updateSkill, deleteSkill } =
    useSkillStore();
  const { agents } = useAgentStore();

  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [deleting, setDeleting] = useState(false);

  // Edit form state
  const [description, setDescription] = useState("");
  const [version, setVersion] = useState("");
  const [author, setAuthor] = useState("");
  const [category, setCategory] = useState("general");
  const [icon, setIcon] = useState("");
  const [autoInject, setAutoInject] = useState(false);
  const [triggers, setTriggers] = useState<string[]>([]);
  const [methodology, setMethodology] = useState("");

  useEffect(() => {
    fetchSkillDetail(skillName);
  }, [skillName, fetchSkillDetail]);

  useEffect(() => {
    if (selectedSkill) {
      setDescription(selectedSkill.description);
      setVersion(selectedSkill.version);
      setAuthor(selectedSkill.author);
      setCategory(selectedSkill.category);
      setIcon(selectedSkill.icon);
      setAutoInject(selectedSkill.auto_inject);
      setTriggers(selectedSkill.triggers);
      setMethodology(selectedSkill.methodology);
    }
  }, [selectedSkill]);

  if (!selectedSkill) {
    return (
      <div className="flex items-center justify-center h-32">
        <span className="loading loading-spinner loading-md text-primary" />
      </div>
    );
  }

  const s = selectedSkill;

  const handleToggle = async (agentId: string) => {
    const isUsing = s.agents_using.includes(agentId);
    const ok = isUsing
      ? await disableSkill(skillName, agentId)
      : await enableSkill(skillName, agentId);
    if (ok) fetchSkillDetail(skillName);
  };

  const handleSave = async () => {
    setSaving(true);
    const ok = await updateSkill(skillName, {
      description, version, author, category, icon,
      auto_inject: autoInject, triggers, methodology,
    });
    if (ok) {
      await fetchSkillDetail(skillName);
      setEditing(false);
    }
    setSaving(false);
  };

  const handleDelete = async () => {
    setDeleting(true);
    const result = await deleteSkill(skillName);
    if (result.deleted) onBack();
    setDeleting(false);
  };

  const cancelEdit = () => {
    setEditing(false);
    setDescription(s.description);
    setVersion(s.version);
    setAuthor(s.author);
    setCategory(s.category);
    setIcon(s.icon);
    setAutoInject(s.auto_inject);
    setTriggers(s.triggers);
    setMethodology(s.methodology);
  };

  return (
    <div className="h-full flex flex-col">
      <div className="px-6 py-4 border-b border-neutral">
        <button onClick={onBack} className="btn btn-ghost btn-xs mb-2">
          &larr; Back to Skills
        </button>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <h1 className="text-xl font-bold text-base-content">{s.name}</h1>
            <span className="badge badge-sm badge-ghost">v{s.version}</span>
            {s.is_builtin && <span className="badge badge-sm badge-ghost">built-in</span>}
            {s.auto_inject && <span className="badge badge-sm badge-accent">auto-inject</span>}
          </div>
          {!s.is_builtin && !editing && (
            <button onClick={() => setEditing(true)} className="btn btn-ghost btn-sm">Edit</button>
          )}
          {editing && (
            <div className="flex gap-2">
              <button onClick={cancelEdit} className="btn btn-ghost btn-sm">Cancel</button>
              <button onClick={handleSave} disabled={saving} className="btn btn-primary btn-sm">
                {saving ? <span className="loading loading-spinner loading-xs" /> : "Save"}
              </button>
            </div>
          )}
        </div>
        {!editing && <p className="text-xs text-base-content/60 mt-1">{s.description}</p>}
      </div>

      <div className="flex-1 overflow-y-auto p-6">
        <div className="max-w-xl mx-auto space-y-6">
          {editing ? (
            <SkillEditForm
              {...{ description, setDescription, version, setVersion, author, setAuthor,
                category, setCategory, icon, setIcon, autoInject, setAutoInject,
                triggers, setTriggers, methodology, setMethodology }}
            />
          ) : (
            <ViewMode skill={s} agents={agents} onToggle={handleToggle} />
          )}

          {!s.is_builtin && !editing && (
            <div className="border border-error/30 rounded-lg p-4 space-y-3">
              <h3 className="text-sm font-semibold text-error">Danger Zone</h3>
              <p className="text-xs text-base-content/60">
                Permanently remove this skill. It will be disabled for all agents.
              </p>
              {!confirmDelete ? (
                <button onClick={() => setConfirmDelete(true)} className="btn btn-error btn-sm btn-outline">
                  Remove Skill
                </button>
              ) : (
                <span className="flex items-center gap-2">
                  <span className="text-xs text-error">Are you sure?</span>
                  <button onClick={handleDelete} disabled={deleting} className="btn btn-error btn-xs">
                    {deleting ? <span className="loading loading-spinner loading-xs" /> : "Yes, delete"}
                  </button>
                  <button onClick={() => setConfirmDelete(false)} className="btn btn-ghost btn-xs">No</button>
                </span>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function ViewMode({ skill: s, agents, onToggle }: { skill: any; agents: any[]; onToggle: (id: string) => void }) {
  return (
    <>
      <Section title="Methodology">
        <pre className="whitespace-pre-wrap text-sm font-mono text-base-content/80 bg-base-300 rounded-lg p-4 max-h-96 overflow-y-auto">
          {s.methodology}
        </pre>
      </Section>
      {s.triggers.length > 0 && (
        <Section title="Trigger Keywords">
          <div className="flex flex-wrap gap-1.5">
            {s.triggers.map((t: string) => <span key={t} className="badge badge-sm badge-outline">{t}</span>)}
          </div>
        </Section>
      )}
      <Section title="Enabled For">
        <div className="space-y-2">
          {agents.filter((a) => a.id !== "huddle").map((a) => (
            <label key={a.id} className="flex items-center gap-3 cursor-pointer">
              <input type="checkbox" className="toggle toggle-sm toggle-primary" checked={s.agents_using.includes(a.id)} onChange={() => onToggle(a.id)} />
              <span className="text-sm">{a.name}</span>
            </label>
          ))}
        </div>
      </Section>
      <Section title="Info">
        <div className="grid grid-cols-2 gap-2 text-xs text-base-content/60">
          <span>Author</span><span className="text-base-content">{s.author}</span>
          <span>Category</span><span className="text-base-content">{s.category}</span>
          <span>Version</span><span className="text-base-content">{s.version}</span>
          <span>Icon</span><span className="text-base-content">{s.icon || "none"}</span>
        </div>
      </Section>
    </>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return <div><h3 className="text-sm font-semibold text-base-content/80 mb-2">{title}</h3>{children}</div>;
}
