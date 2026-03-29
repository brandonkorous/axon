import type { AnalyticsData } from "../../stores/analyticsStore";

function formatCost(cost: number): string {
  if (cost < 0.01) return `$${cost.toFixed(4)}`;
  return `$${cost.toFixed(2)}`;
}

function formatTokens(tokens: number): string {
  if (tokens >= 1_000_000) return `${(tokens / 1_000_000).toFixed(1)}M`;
  if (tokens >= 1_000) return `${(tokens / 1_000).toFixed(1)}k`;
  return String(tokens);
}

function Stat({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <div className="card card-border bg-base-300/30">
      <div className="card-body p-4">
        <div className="text-xs text-base-content/60">{label}</div>
        <div className="text-xl font-bold text-base-content tracking-tight">{value}</div>
        {sub && <div className="text-[10px] text-base-content/50 mt-0.5">{sub}</div>}
      </div>
    </div>
  );
}

export function KpiCards({ data }: { data: AnalyticsData }) {
  const { totals, tasks } = data;

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
      <Stat label="Active Agents" value={String(totals.total_agents)} />
      <Stat
        label="Avg Confidence"
        value={`${(totals.avg_confidence * 100).toFixed(0)}%`}
        sub={`${totals.total_vault_files} vault files`}
      />
      <Stat
        label="Task Completion"
        value={`${tasks.completion_rate}%`}
        sub={`${tasks.completed} of ${tasks.total}`}
      />
      <Stat
        label="Knowledge Graph"
        value={formatTokens(totals.total_vault_files)}
        sub={`${totals.total_links} links`}
      />
      <Stat
        label="Total Cost"
        value={formatCost(totals.total_cost)}
        sub={`${totals.total_requests.toLocaleString()} requests`}
      />
      <Stat
        label="Token Usage"
        value={formatTokens(totals.total_tokens)}
        sub={totals.total_requests > 0
          ? `~${formatTokens(Math.round(totals.total_tokens / totals.total_requests))}/req`
          : ""}
      />
    </div>
  );
}
