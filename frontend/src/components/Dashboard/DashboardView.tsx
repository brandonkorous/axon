import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useAgentStore } from "../../stores/agentStore";
import { StatusBadge } from "../AgentControls/AgentControls";
import { orgApiPath } from "../../stores/orgStore";
import { PRIORITY_BADGE, STATUS_BADGE } from "../../constants/badges";

interface TaskSummary {
  counts: Record<string, number>;
  total: number;
  recent: Array<{
    path: string;
    name: string;
    status: string;
    priority: string;
    assignee: string;
  }>;
}

interface IssueSummary {
  counts: Record<string, number>;
  total: number;
  recent: Array<{
    path: string;
    name: string;
    id: number;
    status: string;
    priority: string;
    assignee: string;
  }>;
}

interface AuditSummary {
  total: number;
  recent: Array<{
    timestamp: string;
    agent_id: string;
    action: string;
    tool: string;
  }>;
}

interface AchievementSummary {
  name: string;
  impact: string;
  date: string;
  agents_involved: string[];
}

interface Decision {
  vault: string;
  path: string;
  name: string;
  description: string;
  date: string;
}

interface DashboardData {
  agents: Array<{
    id: string;
    name: string;
    title: string;
    color: string;
    status: string;
    vault_files: number;
    message_count: number;
  }>;
  recent_decisions: Decision[];
  pending_actions: Array<Record<string, unknown>>;
  tasks: TaskSummary;
  issues: IssueSummary;
  audit: AuditSummary;
  achievements: AchievementSummary[];
}


const ACTION_COLORS: Record<string, string> = {
  vault_write: "text-accent",
  vault_read: "text-info",
  task_create: "text-success",
  task_update: "text-warning",
  issue_create: "text-error",
  delegation: "text-info",
};

function formatTime(ts: string): string {
  if (!ts) return "";
  const d = new Date(ts);
  const now = new Date();
  const diffMs = now.getTime() - d.getTime();
  const diffMin = Math.floor(diffMs / 60000);
  if (diffMin < 1) return "just now";
  if (diffMin < 60) return `${diffMin}m ago`;
  const diffHr = Math.floor(diffMin / 60);
  if (diffHr < 24) return `${diffHr}h ago`;
  return d.toLocaleDateString();
}

export function DashboardView() {
  const { agents } = useAgentStore();
  const [data, setData] = useState<DashboardData | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    setError(false);
    fetch(orgApiPath("dashboard"))
      .then((r) => r.json())
      .then(setData)
      .catch(() => setError(true));
  }, []);

  return (
    <div className="h-full overflow-y-auto p-6 space-y-6">
      <h1 className="text-2xl font-bold text-base-content">Command Center</h1>
      {error && (
        <div className="flex items-center gap-3 p-3 rounded-lg bg-error/10 border border-error/20 text-error text-sm">
          Failed to load dashboard data.
          <button onClick={() => { setError(false); fetch(orgApiPath("dashboard")).then((r) => r.json()).then(setData).catch(() => setError(true)); }} className="btn btn-ghost btn-xs text-error">Retry</button>
        </div>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {agents
          .filter((a) => a.id !== "axon")
          .map((agent) => (
            <Link
              key={agent.id}
              to={`/agent/${agent.id}`}
              className="card card-border bg-base-300/50 hover:bg-base-300 transition-colors focus-visible:ring-2 focus-visible:ring-primary focus-visible:outline-none"
            >
              <div className="card-body p-4">
                <div className="flex items-center gap-3">
                  <div
                    className="w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold text-white"
                    style={{ backgroundColor: agent.ui.color }}
                    aria-hidden="true"
                  >
                    {agent.name[0]}
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-base-content">{agent.name}</span>
                      {agent.lifecycle && agent.lifecycle.status !== "active" && (
                        <StatusBadge status={agent.lifecycle.status} />
                      )}
                    </div>
                    <div className="text-xs text-neutral-content">{agent.title}</div>
                  </div>
                </div>
              </div>
            </Link>
          ))}

        <Link
          to="/huddle"
          className="card card-border bg-base-300/50 hover:bg-base-300 transition-colors focus-visible:ring-2 focus-visible:ring-primary focus-visible:outline-none"
        >
          <div className="card-body p-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-warning flex items-center justify-center text-sm font-bold text-warning-content">
                H
              </div>
              <div>
                <div className="font-semibold text-base-content">Huddle</div>
                <div className="text-xs text-neutral-content">Group Session</div>
              </div>
            </div>
          </div>
        </Link>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card card-border bg-base-300/30">
          <div className="card-body p-5">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-base font-semibold text-base-content">Tasks</h2>
              <Link to="/tasks" className="link link-accent text-xs focus-visible:ring-2 focus-visible:ring-primary focus-visible:outline-none rounded">View all</Link>
            </div>
            {data?.tasks && data.tasks.total > 0 ? (
              <>
                <div className="flex gap-3 mb-4">
                  {Object.entries(data.tasks.counts).map(([status, count]) => (
                    <div key={status} className="text-center">
                      <div className="text-lg font-bold text-base-content">{count}</div>
                      <div className="text-[10px] text-neutral-content capitalize">{status.replace("_", " ")}</div>
                    </div>
                  ))}
                </div>
                <div className="space-y-2">
                  {data.tasks.recent.map((t) => (
                    <div key={t.path} className="flex items-center justify-between py-1.5 border-t border-neutral/30">
                      <div className="flex items-center gap-2 min-w-0">
                        <span className={`badge badge-soft badge-xs ${STATUS_BADGE[t.status] || "badge-ghost"}`}>{t.status.replace("_", " ")}</span>
                        <span className="text-sm text-base-content/80 truncate">{t.name}</span>
                      </div>
                      <div className="flex items-center gap-2 shrink-0">
                        {t.assignee && <span className="text-[10px] text-neutral-content">{t.assignee}</span>}
                        <span className={`text-[10px] font-mono ${PRIORITY_BADGE[t.priority] || "text-neutral-content"}`}>{t.priority}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </>
            ) : (
              <p className="text-sm text-neutral-content">No tasks yet.</p>
            )}
          </div>
        </div>

        <div className="card card-border bg-base-300/30">
          <div className="card-body p-5">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-base font-semibold text-base-content">Issues</h2>
              <Link to="/issues" className="link link-accent text-xs focus-visible:ring-2 focus-visible:ring-primary focus-visible:outline-none rounded">View all</Link>
            </div>
            {data?.issues && data.issues.total > 0 ? (
              <>
                <div className="flex gap-3 mb-4">
                  {Object.entries(data.issues.counts).map(([status, count]) => (
                    <div key={status} className="text-center">
                      <div className="text-lg font-bold text-base-content">{count}</div>
                      <div className="text-[10px] text-neutral-content capitalize">{status.replace("_", " ")}</div>
                    </div>
                  ))}
                </div>
                <div className="space-y-2">
                  {data.issues.recent.map((issue) => (
                    <div key={issue.path} className="flex items-center justify-between py-1.5 border-t border-neutral/30">
                      <div className="flex items-center gap-2 min-w-0">
                        <span className="text-[10px] text-neutral-content font-mono">#{issue.id}</span>
                        <span className={`badge badge-soft badge-xs ${STATUS_BADGE[issue.status] || "badge-ghost"}`}>{issue.status.replace("_", " ")}</span>
                        <span className="text-sm text-base-content/80 truncate">{issue.name}</span>
                      </div>
                      <span className={`text-[10px] font-mono shrink-0 ${PRIORITY_BADGE[issue.priority] || "text-neutral-content"}`}>{issue.priority}</span>
                    </div>
                  ))}
                </div>
              </>
            ) : (
              <p className="text-sm text-neutral-content">No issues yet.</p>
            )}
          </div>
        </div>

        <div className="card card-border bg-base-300/30">
          <div className="card-body p-5">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-base font-semibold text-base-content">Audit Log</h2>
              <Link to="/audit" className="link link-accent text-xs focus-visible:ring-2 focus-visible:ring-primary focus-visible:outline-none rounded">View all</Link>
            </div>
            {data?.audit && data.audit.total > 0 ? (
              <>
                <div className="text-xs text-neutral-content mb-3">{data.audit.total.toLocaleString()} total entries</div>
                <div className="space-y-1.5">
                  {data.audit.recent.map((entry, i) => (
                    <div key={i} className="flex items-center justify-between py-1 text-xs">
                      <div className="flex items-center gap-2 min-w-0">
                        <span className="text-neutral-content shrink-0">{entry.agent_id}</span>
                        <span className={`font-medium ${ACTION_COLORS[entry.action] || "text-neutral-content"}`}>{entry.action}</span>
                      </div>
                      <span className="text-neutral-content/60 shrink-0">{formatTime(entry.timestamp)}</span>
                    </div>
                  ))}
                </div>
              </>
            ) : (
              <p className="text-sm text-neutral-content">No audit entries yet.</p>
            )}
          </div>
        </div>

        <div className="card card-border bg-base-300/30">
          <div className="card-body p-5">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-base font-semibold text-base-content">Achievements</h2>
              <Link to="/achievements" className="link link-accent text-xs focus-visible:ring-2 focus-visible:ring-primary focus-visible:outline-none rounded">View all</Link>
            </div>
            {data?.achievements && data.achievements.length > 0 ? (
              <div className="space-y-3">
                {data.achievements.map((a, i) => (
                  <div key={i} className="border-t border-neutral/30 pt-2 first:border-0 first:pt-0">
                    <div className="text-sm font-medium text-base-content">{a.name}</div>
                    {a.impact && <div className="text-xs text-success mt-0.5">{a.impact}</div>}
                    <div className="flex items-center gap-2 mt-1">
                      {a.agents_involved?.map((agent) => (
                        <span key={agent} className="badge badge-soft badge-info badge-xs">{agent}</span>
                      ))}
                      <span className="text-[10px] text-neutral-content/60">{a.date}</span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-neutral-content">No achievements yet.</p>
            )}
          </div>
        </div>
      </div>

      {data?.recent_decisions && data.recent_decisions.length > 0 && (
        <div className="card card-border bg-base-300/30">
          <div className="card-body p-5">
            <h2 className="text-base font-semibold text-base-content mb-4">Recent Decisions</h2>
            <div className="space-y-2">
              {data.recent_decisions.map((d, i) => (
                <div key={i} className="flex items-center justify-between py-1.5 border-t border-neutral/30 first:border-0">
                  <div>
                    <span className="text-sm font-medium text-base-content">{d.name}</span>
                    <span className="text-xs text-neutral-content ml-2">({d.vault})</span>
                  </div>
                  <span className="text-xs text-neutral-content">{d.date}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
