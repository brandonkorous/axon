import { useEffect, useState } from "react";
import { useSkillStore, type SkillInfo } from "../../stores/skillStore";
import { SkillDetail } from "./SkillDetail";

const CATEGORY_LABELS: Record<string, string> = {
  research: "Research",
  integration: "Integrations",
  media: "Media",
  browser: "Browser",
  general: "General",
};

export function SkillBrowser() {
  const { skills, loading, fetchSkills } = useSkillStore();
  const [selectedSkill, setSelectedSkill] = useState<string | null>(null);

  useEffect(() => {
    fetchSkills();
  }, [fetchSkills]);

  if (selectedSkill) {
    return <SkillDetail skillName={selectedSkill} onBack={() => setSelectedSkill(null)} />;
  }

  const grouped = groupByCategory(skills);

  return (
    <div className="h-full flex flex-col">
      <div className="px-6 py-4 border-b border-neutral">
        <h1 className="text-xl font-bold text-base-content">Skills</h1>
        <p className="text-xs text-base-content/60 mt-1">
          Capabilities that agents can load on demand
        </p>
      </div>

      <div className="flex-1 overflow-y-auto p-6">
        {loading && skills.length === 0 ? (
          <div className="flex items-center justify-center h-32">
            <span className="loading loading-spinner loading-md text-primary" />
          </div>
        ) : skills.length === 0 ? (
          <p className="text-sm text-base-content/60 text-center mt-12">
            No skills registered yet
          </p>
        ) : (
          <div className="max-w-2xl mx-auto space-y-6">
            {Object.entries(grouped).map(([category, categorySkills]) => (
              <div key={category}>
                <h2 className="text-sm font-semibold text-base-content/80 mb-2">
                  {CATEGORY_LABELS[category] || category}
                </h2>
                <div className="space-y-2">
                  {categorySkills.map((skill) => (
                    <SkillCard
                      key={skill.name}
                      skill={skill}
                      onClick={() => setSelectedSkill(skill.name)}
                    />
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function SkillCard({ skill, onClick }: { skill: SkillInfo; onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      className="card bg-base-300 border border-neutral w-full text-left hover:border-primary/30 transition-colors"
    >
      <div className="card-body p-4 flex-row items-center gap-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <p className="text-sm font-medium">{skill.name}</p>
            <span className="badge badge-xs badge-ghost">v{skill.version}</span>
            {skill.auto_load && (
              <span className="badge badge-xs badge-accent">auto</span>
            )}
          </div>
          <p className="text-xs text-base-content/60 truncate mt-0.5">
            {skill.description}
          </p>
        </div>
        <div className="text-xs text-base-content/40">
          {skill.tools.length} tool{skill.tools.length !== 1 ? "s" : ""}
        </div>
      </div>
    </button>
  );
}

function groupByCategory(skills: SkillInfo[]): Record<string, SkillInfo[]> {
  const groups: Record<string, SkillInfo[]> = {};
  for (const skill of skills) {
    const cat = skill.category || "general";
    if (!groups[cat]) groups[cat] = [];
    groups[cat].push(skill);
  }
  return groups;
}
