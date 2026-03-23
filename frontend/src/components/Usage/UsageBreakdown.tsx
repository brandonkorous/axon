import type { BreakdownEntry } from "../../stores/usageStore";

interface Props {
  title: string;
  data: Record<string, BreakdownEntry>;
  totalCost: number;
}

function formatCost(cost: number): string {
  if (cost < 0.01) return `$${cost.toFixed(4)}`;
  return `$${cost.toFixed(2)}`;
}

function formatTokens(tokens: number): string {
  if (tokens >= 1_000_000) return `${(tokens / 1_000_000).toFixed(1)}M`;
  if (tokens >= 1_000) return `${(tokens / 1_000).toFixed(1)}k`;
  return String(tokens);
}

export function UsageBreakdown({ title, data, totalCost }: Props) {
  const entries = Object.entries(data);

  return (
    <div className="card card-border bg-base-300/30">
      <div className="card-body p-5">
        <h2 className="text-base font-semibold text-base-content mb-4">
          {title}
        </h2>
        {entries.length === 0 ? (
          <p className="text-sm text-neutral-content">No data yet.</p>
        ) : (
          <div className="space-y-3">
            {entries.map(([name, entry]) => {
              const pct = totalCost > 0 ? (entry.cost / totalCost) * 100 : 0;
              return (
                <div key={name}>
                  <div className="flex items-center justify-between text-xs mb-1">
                    <span
                      className="text-base-content font-medium truncate max-w-[60%]"
                      title={name}
                    >
                      {name || "(unknown)"}
                    </span>
                    <div className="flex items-center gap-3 text-neutral-content shrink-0">
                      <span>{entry.count} req</span>
                      <span>{formatTokens(entry.tokens)} tok</span>
                      <span className="text-base-content font-medium">
                        {formatCost(entry.cost)}
                      </span>
                    </div>
                  </div>
                  <progress
                    className="progress progress-accent w-full h-1.5"
                    value={pct}
                    max={100}
                    aria-label={`${name}: ${pct.toFixed(0)}% of total cost`}
                  />
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
