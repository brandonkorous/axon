interface ToolUsagePanelProps {
  toolUsage: Record<string, number>;
}

const TOOL_COLORS: Record<string, string> = {
  memory_write: "bg-accent",
  memory_read: "bg-info",
  file_write: "bg-accent",
  file_read: "bg-info",
  code_execute: "bg-warning",
  task_create: "bg-success",
  task_update: "bg-success/60",
  issue_create: "bg-error",
  delegation: "bg-primary",
  web_search: "bg-secondary",
};

export function ToolUsagePanel({ toolUsage }: ToolUsagePanelProps) {
  const entries = Object.entries(toolUsage);
  const max = entries.length > 0 ? entries[0][1] : 1;
  const total = entries.reduce((s, [, v]) => s + v, 0);

  return (
    <div className="card card-border bg-base-300/30">
      <div className="card-body p-5">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-base font-semibold text-base-content">Tool Usage</h2>
          <span className="text-xs text-base-content/50">{total.toLocaleString()} total</span>
        </div>
        {entries.length === 0 ? (
          <p className="text-xs text-base-content/40">No tool usage data yet.</p>
        ) : (
          <div className="space-y-2">
            {entries.slice(0, 12).map(([tool, count]) => {
              const pct = (count / max) * 100;
              const bg = TOOL_COLORS[tool] || "bg-base-content/20";
              return (
                <div key={tool} className="flex items-center gap-2">
                  <span className="text-xs text-base-content/70 w-28 truncate text-right font-mono">
                    {tool}
                  </span>
                  <div className="flex-1 h-2 bg-base-content/10 rounded-full overflow-hidden">
                    <div className={`h-full rounded-full ${bg}`} style={{ width: `${pct}%` }} />
                  </div>
                  <span className="text-xs tabular-nums text-base-content/60 w-10 text-right">
                    {count}
                  </span>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
