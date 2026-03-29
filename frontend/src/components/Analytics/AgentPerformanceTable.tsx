import { Link } from "react-router-dom";
import type { AgentMetrics } from "../../stores/analyticsStore";

function formatCost(cost: number): string {
  if (cost < 0.01) return `$${cost.toFixed(4)}`;
  return `$${cost.toFixed(2)}`;
}

function ConfidenceBar({ value }: { value: number }) {
  const pct = Math.round(value * 100);
  const color = pct >= 80 ? "bg-success" : pct >= 50 ? "bg-warning" : "bg-error";
  return (
    <div className="flex items-center gap-2">
      <div className="w-16 h-1.5 bg-base-content/10 rounded-full overflow-hidden">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs text-base-content/70 tabular-nums">{pct}%</span>
    </div>
  );
}

function ConfidenceDistribution({ high, medium, low }: { high: number; medium: number; low: number }) {
  const total = high + medium + low;
  if (total === 0) return <span className="text-xs text-base-content/40">-</span>;
  return (
    <div className="flex items-center gap-1">
      {high > 0 && <span className="badge badge-success badge-xs">{high}</span>}
      {medium > 0 && <span className="badge badge-warning badge-xs">{medium}</span>}
      {low > 0 && <span className="badge badge-error badge-xs">{low}</span>}
    </div>
  );
}

export function AgentPerformanceTable({ agents }: { agents: AgentMetrics[] }) {
  const sorted = [...agents].sort((a, b) => b.confidence.current_avg - a.confidence.current_avg);

  return (
    <div className="card card-border bg-base-300/30">
      <div className="card-body p-5">
        <h2 className="text-base font-semibold text-base-content mb-4">Agent Performance</h2>
        <div className="overflow-x-auto">
          <table className="table table-sm">
            <thead>
              <tr className="text-xs text-base-content/60">
                <th>Agent</th>
                <th>Confidence</th>
                <th>Distribution</th>
                <th>Memory</th>
                <th>Links</th>
                <th>Messages</th>
                <th>Cost</th>
                <th>Tokens</th>
              </tr>
            </thead>
            <tbody>
              {sorted.map((agent) => (
                <tr key={agent.id} className="hover">
                  <td>
                    <Link to={`/agent/${agent.id}`} className="flex items-center gap-2 group">
                      <span
                        className="w-2.5 h-2.5 rounded-full shrink-0"
                        style={{ backgroundColor: agent.color }}
                      />
                      <span className="font-medium text-sm text-base-content group-hover:text-primary transition-colors">
                        {agent.name}
                      </span>
                      {agent.status !== "active" && (
                        <span className="badge badge-ghost badge-xs">{agent.status}</span>
                      )}
                    </Link>
                  </td>
                  <td><ConfidenceBar value={agent.confidence.current_avg} /></td>
                  <td>
                    <ConfidenceDistribution
                      high={agent.confidence.high}
                      medium={agent.confidence.medium}
                      low={agent.confidence.low}
                    />
                  </td>
                  <td>
                    <span className="text-sm tabular-nums">
                      {agent.memory.active}
                      {agent.memory.archived > 0 && (
                        <span className="text-base-content/40 text-xs ml-1">+{agent.memory.archived}</span>
                      )}
                    </span>
                  </td>
                  <td><span className="text-sm tabular-nums">{agent.memory.total_links}</span></td>
                  <td><span className="text-sm tabular-nums">{agent.message_count}</span></td>
                  <td><span className="text-sm tabular-nums">{formatCost(agent.usage.cost)}</span></td>
                  <td><span className="text-sm tabular-nums">{agent.usage.tokens.toLocaleString()}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
