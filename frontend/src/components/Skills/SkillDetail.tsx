import { useEffect } from "react";
import { useSkillStore } from "../../stores/skillStore";
import { useAgentStore } from "../../stores/agentStore";

export function SkillDetail({ skillName, onBack }: { skillName: string; onBack: () => void }) {
  const { selectedSkill, fetchSkillDetail, enableSkill, disableSkill } = useSkillStore();
  const { agents } = useAgentStore();

  useEffect(() => {
    fetchSkillDetail(skillName);
  }, [skillName, fetchSkillDetail]);

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

  return (
    <div className="h-full flex flex-col">
      <div className="px-6 py-4 border-b border-neutral">
        <button onClick={onBack} className="btn btn-ghost btn-xs mb-2">
          &larr; Back to Skills
        </button>
        <div className="flex items-center gap-3">
          <h1 className="text-xl font-bold text-base-content">{s.name}</h1>
          <span className="badge badge-sm badge-ghost">v{s.version}</span>
          {s.auto_load && <span className="badge badge-sm badge-accent">auto-load</span>}
        </div>
        <p className="text-xs text-base-content/60 mt-1">{s.description}</p>
      </div>

      <div className="flex-1 overflow-y-auto p-6">
        <div className="max-w-xl mx-auto space-y-6">
          {/* Tools */}
          <Section title="Tools">
            <div className="space-y-1.5">
              {s.tools.map((t: any) => (
                <div key={typeof t === "string" ? t : t.name} className="flex items-start gap-2">
                  <code className="text-xs font-mono text-primary shrink-0">
                    {typeof t === "string" ? t : t.name}
                  </code>
                  {typeof t !== "string" && t.description && (
                    <span className="text-xs text-base-content/60">{t.description}</span>
                  )}
                </div>
              ))}
            </div>
          </Section>

          {/* Triggers */}
          {s.triggers.length > 0 && (
            <Section title="Trigger Keywords">
              <div className="flex flex-wrap gap-1.5">
                {s.triggers.map((t) => (
                  <span key={t} className="badge badge-sm badge-outline">{t}</span>
                ))}
              </div>
            </Section>
          )}

          {/* Agent Enablement */}
          <Section title="Enabled For">
            <div className="space-y-2">
              {agents
                .filter((a) => a.id !== "huddle")
                .map((a) => {
                  const enabled = s.agents_using.includes(a.id);
                  return (
                    <label key={a.id} className="flex items-center gap-3 cursor-pointer">
                      <input
                        type="checkbox"
                        className="toggle toggle-sm toggle-primary"
                        checked={enabled}
                        onChange={() => handleToggle(a.id)}
                      />
                      <span className="text-sm">{a.name}</span>
                    </label>
                  );
                })}
            </div>
          </Section>

          {/* Dependencies */}
          {s.python_deps?.length > 0 && (
            <Section title="Python Dependencies">
              <div className="flex flex-wrap gap-1.5">
                {s.python_deps.map((d) => (
                  <code key={d} className="text-xs font-mono badge badge-sm badge-ghost">{d}</code>
                ))}
              </div>
            </Section>
          )}

          {/* Credentials */}
          {s.required_credentials?.length > 0 && (
            <Section title="Required Credentials">
              <div className="flex flex-wrap gap-1.5">
                {s.required_credentials.map((c) => (
                  <span key={c} className="badge badge-sm badge-warning badge-outline">{c}</span>
                ))}
              </div>
            </Section>
          )}

          {/* Metadata */}
          <Section title="Info">
            <div className="grid grid-cols-2 gap-2 text-xs text-base-content/60">
              <span>Author</span><span className="text-base-content">{s.author}</span>
              <span>Category</span><span className="text-base-content">{s.category}</span>
              <span>Version</span><span className="text-base-content">{s.version}</span>
            </div>
          </Section>
        </div>
      </div>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div>
      <h3 className="text-sm font-semibold text-base-content/80 mb-2">{title}</h3>
      {children}
    </div>
  );
}
