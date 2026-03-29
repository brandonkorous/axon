import type { AgentMetrics } from "../../stores/analyticsStore";

function Sparkline({ data, color }: { data: Array<{ date: string; avg: number }>; color: string }) {
  if (data.length < 2) return <span className="text-xs text-base-content/40">No history</span>;

  const width = 120;
  const height = 32;
  const min = Math.min(...data.map((d) => d.avg));
  const max = Math.max(...data.map((d) => d.avg));
  const range = max - min || 0.1;

  const points = data.map((d, i) => {
    const x = (i / (data.length - 1)) * width;
    const y = height - ((d.avg - min) / range) * (height - 4) - 2;
    return `${x},${y}`;
  });

  return (
    <svg width={width} height={height} className="overflow-visible">
      <polyline
        points={points.join(" ")}
        fill="none"
        stroke={color}
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      {data.length > 0 && (
        <circle
          cx={width}
          cy={height - ((data[data.length - 1].avg - min) / range) * (height - 4) - 2}
          r="2"
          fill={color}
        />
      )}
    </svg>
  );
}

function ConfBar({ label, value, total, color }: { label: string; value: number; total: number; color: string }) {
  const pct = total > 0 ? (value / total) * 100 : 0;
  return (
    <div className="flex items-center gap-2">
      <span className="text-[10px] text-base-content/60 w-14 text-right">{label}</span>
      <div className="flex-1 h-2 bg-base-content/10 rounded-full overflow-hidden">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs tabular-nums text-base-content/70 w-8 text-right">{value}</span>
    </div>
  );
}

export function ConfidencePanel({ agents }: { agents: AgentMetrics[] }) {
  const totalFiles = agents.reduce((s, a) => s + a.confidence.total, 0);
  const totalHigh = agents.reduce((s, a) => s + a.confidence.high, 0);
  const totalMedium = agents.reduce((s, a) => s + a.confidence.medium, 0);
  const totalLow = agents.reduce((s, a) => s + a.confidence.low, 0);

  return (
    <div className="card card-border bg-base-300/30">
      <div className="card-body p-5">
        <h2 className="text-base font-semibold text-base-content mb-4">Confidence Overview</h2>

        <div className="space-y-2 mb-5">
          <ConfBar label="High" value={totalHigh} total={totalFiles} color="bg-success" />
          <ConfBar label="Medium" value={totalMedium} total={totalFiles} color="bg-warning" />
          <ConfBar label="Low" value={totalLow} total={totalFiles} color="bg-error" />
        </div>

        <h3 className="text-xs font-medium text-base-content/60 mb-3">Confidence Trends</h3>
        <div className="space-y-3">
          {agents
            .filter((a) => a.confidence.history.length > 0)
            .map((agent) => (
              <div key={agent.id} className="flex items-center gap-3">
                <span
                  className="w-2 h-2 rounded-full shrink-0"
                  style={{ backgroundColor: agent.color }}
                />
                <span className="text-xs text-base-content/80 w-20 truncate">{agent.name}</span>
                <Sparkline data={agent.confidence.history} color={agent.color} />
                <span className="text-xs tabular-nums text-base-content/60 ml-auto">
                  {(agent.confidence.current_avg * 100).toFixed(0)}%
                </span>
              </div>
            ))}
          {agents.every((a) => a.confidence.history.length === 0) && (
            <p className="text-xs text-base-content/40">No confidence history yet.</p>
          )}
        </div>
      </div>
    </div>
  );
}
