import type { AgentMetrics } from "../../stores/analyticsStore";

function TypeBreakdown({ agents }: { agents: AgentMetrics[] }) {
  const merged: Record<string, number> = {};
  for (const agent of agents) {
    for (const [type, count] of Object.entries(agent.memory.by_type)) {
      merged[type] = (merged[type] || 0) + count;
    }
  }
  const entries = Object.entries(merged).sort((a, b) => b[1] - a[1]);
  const max = entries.length > 0 ? entries[0][1] : 1;

  if (entries.length === 0) return null;

  return (
    <div className="space-y-1.5">
      {entries.slice(0, 8).map(([type, count]) => (
        <div key={type} className="flex items-center gap-2">
          <span className="text-[10px] text-base-content/60 w-20 truncate text-right capitalize">
            {type.replace(/_/g, " ")}
          </span>
          <div className="flex-1 h-1.5 bg-base-content/10 rounded-full overflow-hidden">
            <div
              className="h-full rounded-full bg-accent/60"
              style={{ width: `${(count / max) * 100}%` }}
            />
          </div>
          <span className="text-[10px] tabular-nums text-base-content/50 w-6 text-right">{count}</span>
        </div>
      ))}
    </div>
  );
}

export function MemoryPanel({ agents }: { agents: AgentMetrics[] }) {
  const totalFiles = agents.reduce((s, a) => s + a.memory.total_files, 0);
  const totalActive = agents.reduce((s, a) => s + a.memory.active, 0);
  const totalArchived = agents.reduce((s, a) => s + a.memory.archived, 0);
  const totalLinks = agents.reduce((s, a) => s + a.memory.total_links, 0);
  const linkDensity = totalFiles > 0 ? (totalLinks / totalFiles).toFixed(1) : "0";

  return (
    <div className="card card-border bg-base-300/30">
      <div className="card-body p-5">
        <h2 className="text-base font-semibold text-base-content mb-4">Knowledge Base</h2>

        <div className="grid grid-cols-2 gap-3 mb-5">
          <div>
            <div className="text-lg font-bold text-base-content tabular-nums">{totalFiles}</div>
            <div className="text-[10px] text-base-content/60">Total files</div>
          </div>
          <div>
            <div className="text-lg font-bold text-base-content tabular-nums">{totalLinks}</div>
            <div className="text-[10px] text-base-content/60">Knowledge links</div>
          </div>
          <div>
            <div className="text-lg font-bold text-base-content tabular-nums">{totalActive}</div>
            <div className="text-[10px] text-base-content/60">
              Active <span className="text-base-content/40">/ {totalArchived} archived</span>
            </div>
          </div>
          <div>
            <div className="text-lg font-bold text-base-content tabular-nums">{linkDensity}</div>
            <div className="text-[10px] text-base-content/60">Links per file</div>
          </div>
        </div>

        <h3 className="text-xs font-medium text-base-content/60 mb-3">By Learning Type</h3>
        <TypeBreakdown agents={agents} />

        <h3 className="text-xs font-medium text-base-content/60 mt-4 mb-3">Per Agent</h3>
        <div className="space-y-2">
          {agents
            .filter((a) => a.memory.total_files > 0)
            .sort((a, b) => b.memory.total_files - a.memory.total_files)
            .map((agent) => (
              <div key={agent.id} className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full shrink-0" style={{ backgroundColor: agent.color }} />
                <span className="text-xs text-base-content/80 w-20 truncate">{agent.name}</span>
                <div className="flex-1 h-1.5 bg-base-content/10 rounded-full overflow-hidden">
                  <div
                    className="h-full rounded-full bg-primary/50"
                    style={{
                      width: `${totalFiles > 0 ? (agent.memory.total_files / totalFiles) * 100 : 0}%`,
                    }}
                  />
                </div>
                <span className="text-[10px] tabular-nums text-base-content/60 w-8 text-right">
                  {agent.memory.total_files}
                </span>
              </div>
            ))}
        </div>
      </div>
    </div>
  );
}
