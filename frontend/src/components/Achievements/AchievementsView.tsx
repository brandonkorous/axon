import { useEffect, useState } from "react";
import { orgApiPath } from "../../stores/orgStore";

interface Achievement {
  path: string;
  name: string;
  type: string;
  agents_involved: string[];
  linked_tasks: string[];
  linked_issues: string[];
  impact: string;
  date: string;
  created_by: string;
  created_at: string;
  body: string;
}

export function AchievementsView() {
  const [achievements, setAchievements] = useState<Achievement[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    setError(false);
    fetch(orgApiPath("achievements"))
      .then((r) => r.json())
      .then((data) => {
        setAchievements(Array.isArray(data) ? data : []);
        setLoading(false);
      })
      .catch(() => { setLoading(false); setError(true); });
  }, []);

  return (
    <div className="h-full overflow-y-auto p-6">
      <h1 className="text-2xl font-bold text-base-content mb-6">Achievements</h1>

      {loading ? (
        <div className="flex justify-center py-12">
          <span className="loading loading-spinner loading-md text-primary" />
        </div>
      ) : error ? (
        <div className="text-center py-12">
          <p className="text-error mb-2">Failed to load achievements.</p>
          <button onClick={() => { setLoading(true); setError(false); fetch(orgApiPath("achievements")).then((r) => r.json()).then((data) => { setAchievements(Array.isArray(data) ? data : []); setLoading(false); }).catch(() => { setLoading(false); setError(true); }); }} className="btn btn-ghost btn-xs text-error">Retry</button>
        </div>
      ) : achievements.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-neutral-content mb-2">No achievements yet.</p>
          <p className="text-xs text-neutral-content/60">
            Agents will record milestones here as they complete work.
          </p>
        </div>
      ) : (
        <div className="relative">
          <div className="absolute left-6 top-0 bottom-0 w-px bg-neutral" />

          <div className="space-y-6">
            {achievements.map((a) => (
              <div key={a.path} className="relative pl-14">
                <div className="absolute left-[19px] top-2 w-3 h-3 rounded-full bg-primary border-2 border-base-100" />

                <div className="text-xs text-neutral-content mb-1">{a.date}</div>

                <div className="card card-border bg-base-300/50">
                  <div className="card-body p-4">
                    <h3 className="text-base font-semibold text-base-content mb-1">
                      {a.name}
                    </h3>

                    {a.impact && (
                      <p className="text-sm text-success mb-2">{a.impact}</p>
                    )}

                    <p className="text-sm text-neutral-content mb-3 whitespace-pre-wrap">
                      {a.body
                        ?.replace(/^# .*\n\n?/, "")
                        .replace(/## Impact\n.*$/, "")
                        .trim()}
                    </p>

                    <div className="flex flex-wrap items-center gap-2">
                      {a.agents_involved?.map((agent) => (
                        <span key={agent} className="badge badge-soft badge-info badge-xs">
                          {agent}
                        </span>
                      ))}
                      {a.linked_tasks?.map((task, i) => (
                        <span key={i} className="badge badge-soft badge-accent badge-xs">
                          {task}
                        </span>
                      ))}
                      <span className="text-[10px] text-neutral-content/60">
                        by {a.created_by}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
