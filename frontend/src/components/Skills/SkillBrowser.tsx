import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useSkillStore, type SkillInfo } from "../../stores/skillStore";
import { SkillDetail } from "./SkillDetail";

const CATEGORY_LABELS: Record<string, string> = {
  research: "Research",
  analysis: "Analysis",
  engineering: "Engineering",
  communication: "Communication",
  planning: "Planning",
  general: "General",
};

export function SkillBrowser() {
  const navigate = useNavigate();
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
      <div className="px-6 py-4 border-b border-neutral flex items-start justify-between">
        <div>
          <h1 className="text-xl font-bold text-base-content">Skills</h1>
          <p className="text-xs text-base-content/60 mt-1">
            Cognitive capabilities and reasoning patterns for your agents
          </p>
        </div>
        <button onClick={() => navigate("/skills/new")} className="btn btn-primary btn-sm">
          New Skill
        </button>
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
      <div className="card-body p-4 gap-1.5">
        <div className="flex items-center gap-2">
          <p className="text-sm font-medium">{skill.name}</p>
          <span className="badge badge-xs badge-ghost">{skill.category}</span>
          {skill.is_builtin && (
            <span className="badge badge-xs badge-ghost">built-in</span>
          )}
          {skill.auto_inject && (
            <span className="badge badge-xs badge-accent">auto-inject</span>
          )}
          <span className="ml-auto text-xs text-base-content/40">
            {skill.triggers.length} trigger{skill.triggers.length !== 1 ? "s" : ""}
          </span>
        </div>
        <p className="text-xs text-base-content/60 truncate">{skill.description}</p>
        {skill.methodology_preview && (
          <p className="text-xs text-base-content/40 truncate font-mono">
            {skill.methodology_preview}
          </p>
        )}
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
