import { useEffect } from "react";
import { Link } from "react-router-dom";
import { useUsageStore, type Period } from "../../stores/usageStore";
import { formatCost, formatTokens } from "../../utils/format";
import { StatusBarPopover } from "./StatusBarPopover";

const PERIOD_LABEL: Record<Period, string> = {
  today: "Today",
  "7d": "7 days",
  "30d": "30 days",
  all: "All time",
};

export function StatusBarUsage() {
  const { summary, period, setPeriod, fetchSummary } = useUsageStore();

  useEffect(() => {
    if (!summary) fetchSummary();
  }, [summary, fetchSummary]);

  const cost = summary?.total_cost ?? 0;
  const tokens = summary?.total_tokens ?? 0;
  const requests = summary?.total_requests ?? 0;

  return (
    <StatusBarPopover
      label={`Usage: ${formatCost(cost)} spent`}
      width="w-72"

      trigger={
        <>
          <span className="w-1.5 h-1.5 rounded-full flex-shrink-0 bg-info/50" />
          <span>{formatCost(cost)}</span>
          <span className="hidden sm:inline">Usage</span>
        </>
      }
    >
      <div className="flex items-center justify-between px-3 py-2 border-b border-base-content/10">
        <span className="text-xs font-medium text-base-content">Usage</span>
        <Link to="/usage" className="text-xs text-primary hover:underline">
          Details
        </Link>
      </div>

      <div className="px-3 py-2 space-y-2">
        {/* Period selector */}
        <div className="flex gap-1">
          {(["today", "7d", "30d", "all"] as Period[]).map((p) => (
            <button
              key={p}
              onClick={() => setPeriod(p)}
              className={`btn btn-xs ${p === period ? "btn-primary" : "btn-ghost"}`}
            >
              {PERIOD_LABEL[p]}
            </button>
          ))}
        </div>

        {/* Stats */}
        <div className="grid grid-cols-3 gap-2 py-1">
          <div>
            <div className="text-base font-semibold text-base-content">
              {formatCost(cost)}
            </div>
            <div className="text-[10px] text-base-content/50">Cost</div>
          </div>
          <div>
            <div className="text-base font-semibold text-base-content">
              {formatTokens(tokens)}
            </div>
            <div className="text-[10px] text-base-content/50">Tokens</div>
          </div>
          <div>
            <div className="text-base font-semibold text-base-content">
              {requests}
            </div>
            <div className="text-[10px] text-base-content/50">Requests</div>
          </div>
        </div>

        {/* Top models */}
        {summary?.by_model && Object.keys(summary.by_model).length > 0 && (
          <div className="border-t border-base-content/10 pt-2">
            <div className="text-[10px] text-base-content/50 mb-1">By model</div>
            {Object.entries(summary.by_model)
              .sort(([, a], [, b]) => b.cost - a.cost)
              .slice(0, 3)
              .map(([model, entry]) => (
                <div
                  key={model}
                  className="flex items-center justify-between text-xs py-0.5"
                >
                  <span className="text-base-content/70 truncate">{model}</span>
                  <span className="text-base-content/50 flex-shrink-0 ml-2">
                    {formatCost(entry.cost)}
                  </span>
                </div>
              ))}
          </div>
        )}
      </div>
    </StatusBarPopover>
  );
}
