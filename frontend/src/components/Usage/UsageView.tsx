import { useEffect, useState } from "react";
import { useUsageStore, type Period } from "../../stores/usageStore";
import { UsageBreakdown } from "./UsageBreakdown";
import { UsageTable } from "./UsageTable";

const PERIODS: { value: Period; label: string }[] = [
  { value: "today", label: "Today" },
  { value: "7d", label: "7 days" },
  { value: "30d", label: "30 days" },
  { value: "all", label: "All time" },
];

function formatCost(cost: number): string {
  if (cost < 0.01) return `$${cost.toFixed(4)}`;
  return `$${cost.toFixed(2)}`;
}

function formatTokens(tokens: number): string {
  if (tokens >= 1_000_000) return `${(tokens / 1_000_000).toFixed(1)}M`;
  if (tokens >= 1_000) return `${(tokens / 1_000).toFixed(1)}k`;
  return String(tokens);
}

const PAGE_SIZE = 50;

export function UsageView() {
  const {
    summary,
    records,
    total,
    loading,
    error,
    period,
    setPeriod,
    fetchSummary,
    fetchRecords,
  } = useUsageStore();
  const [page, setPage] = useState(0);

  useEffect(() => {
    fetchSummary();
    fetchRecords(PAGE_SIZE, 0);
  }, [fetchSummary, fetchRecords]);

  const handlePageChange = (newPage: number) => {
    setPage(newPage);
    fetchRecords(PAGE_SIZE, newPage * PAGE_SIZE);
  };

  const avgCost =
    summary && summary.total_requests > 0
      ? summary.total_cost / summary.total_requests
      : 0;

  return (
    <div className="h-full overflow-y-auto p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-base-content">Usage</h1>
        <div className="join">
          {PERIODS.map((p) => (
            <button
              key={p.value}
              onClick={() => {
                setPeriod(p.value);
                setPage(0);
              }}
              className={`join-item btn btn-xs ${
                period === p.value ? "btn-active btn-accent" : "btn-ghost"
              }`}
            >
              {p.label}
            </button>
          ))}
        </div>
      </div>

      {error && (
        <div className="flex items-center gap-3 p-3 rounded-lg bg-error/10 border border-error/20 text-error text-sm">
          Failed to load usage data.
          <button
            onClick={() => {
              fetchSummary();
              fetchRecords(PAGE_SIZE, page * PAGE_SIZE);
            }}
            className="btn btn-ghost btn-xs text-error"
          >
            Retry
          </button>
        </div>
      )}

      {loading && !summary ? (
        <div className="flex items-center justify-center py-12">
          <span className="loading loading-spinner loading-md text-primary" />
        </div>
      ) : (
        <>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <StatCard
              label="Total Cost"
              value={formatCost(summary?.total_cost ?? 0)}
            />
            <StatCard
              label="Total Tokens"
              value={formatTokens(summary?.total_tokens ?? 0)}
            />
            <StatCard
              label="Requests"
              value={(summary?.total_requests ?? 0).toLocaleString()}
            />
            <StatCard label="Avg Cost / Req" value={formatCost(avgCost)} />
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <UsageBreakdown
              title="By Model"
              data={summary?.by_model ?? {}}
              totalCost={summary?.total_cost ?? 0}
            />
            <UsageBreakdown
              title="By Agent"
              data={summary?.by_agent ?? {}}
              totalCost={summary?.total_cost ?? 0}
            />
          </div>

          <UsageTable
            records={records}
            total={total}
            page={page}
            pageSize={PAGE_SIZE}
            onPageChange={handlePageChange}
          />
        </>
      )}
    </div>
  );
}

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="card card-border bg-base-300/30">
      <div className="card-body p-4">
        <div className="text-xs text-base-content/60">{label}</div>
        <div className="text-xl font-bold text-base-content tracking-tight">
          {value}
        </div>
      </div>
    </div>
  );
}
