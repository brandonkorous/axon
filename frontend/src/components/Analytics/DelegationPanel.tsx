import type { DelegationEdge } from "../../stores/analyticsStore";

export function DelegationPanel({ flow }: { flow: DelegationEdge[] }) {
  const max = flow.length > 0 ? flow[0].count : 1;

  return (
    <div className="card card-border bg-base-300/30">
      <div className="card-body p-5">
        <h2 className="text-base font-semibold text-base-content mb-4">Delegation Flow</h2>
        {flow.length === 0 ? (
          <p className="text-xs text-base-content/40">No delegation data yet.</p>
        ) : (
          <div className="space-y-2.5">
            {flow.slice(0, 10).map((edge, i) => {
              const pct = (edge.count / max) * 100;
              return (
                <div key={i} className="flex items-center gap-2">
                  <span className="text-xs font-medium text-base-content/80 w-20 truncate text-right">
                    {edge.from}
                  </span>
                  <svg viewBox="0 0 16 8" className="w-3 h-2 text-base-content/30 shrink-0">
                    <path d="M0 4h12M10 1l3 3-3 3" fill="none" stroke="currentColor" strokeWidth="1.5" />
                  </svg>
                  <span className="text-xs font-medium text-base-content/80 w-20 truncate">
                    {edge.to}
                  </span>
                  <div className="flex-1 h-2 bg-base-content/10 rounded-full overflow-hidden">
                    <div className="h-full rounded-full bg-primary/50" style={{ width: `${pct}%` }} />
                  </div>
                  <span className="text-xs tabular-nums text-base-content/60 w-8 text-right">
                    {edge.count}
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
