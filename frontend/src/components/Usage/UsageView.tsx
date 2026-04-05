import { useState, useMemo } from "react";
import { useUsageSummary, useUsageRecords } from "../../hooks/useUsage";
import { formatCost, formatTokens } from "../../utils/format";
import { UsageBreakdown } from "./UsageBreakdown";
import { UsageTable } from "./UsageTable";

type Period = "today" | "7d" | "30d" | "all";

const PERIODS: { value: Period; label: string }[] = [
  { value: "today", label: "Today" },
  { value: "7d", label: "7 days" },
  { value: "30d", label: "30 days" },
  { value: "all", label: "All time" },
];

const PAGE_SIZE = 50;

function dateRange(period: Period): { dateFrom: string; dateTo: string } {
  const now = new Date();
  const to = now.toISOString().slice(0, 10);
  if (period === "all") return { dateFrom: "2000-01-01", dateTo: to };
  if (period === "today") return { dateFrom: to, dateTo: to };
  const days = period === "7d" ? 7 : 30;
  const from = new Date(now.getTime() - days * 86400000).toISOString().slice(0, 10);
  return { dateFrom: from, dateTo: to };
}

export function UsageView() {
  const [period, setPeriod] = useState<Period>("30d");
  const [page, setPage] = useState(0);

  const { dateFrom, dateTo } = useMemo(() => dateRange(period), [period]);

  const {
    data: summary,
    isLoading: summaryLoading,
    isError: summaryError,
    refetch: refetchSummary,
  } = useUsageSummary(dateFrom, dateTo);

  const {
    data: recordsData,
    isError: recordsError,
    refetch: refetchRecords,
  } = useUsageRecords(dateFrom, dateTo, PAGE_SIZE, page * PAGE_SIZE);

  const records = recordsData?.records ?? [];
  const total = recordsData?.total ?? 0;
  const loading = summaryLoading;
  const error = summaryError || recordsError;

  const handlePageChange = (newPage: number) => {
    setPage(newPage);
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
          Usage data isn't available right now. Try refreshing the page.
          <button
            onClick={() => {
              refetchSummary();
              refetchRecords();
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
            <StatCard label="Avg Cost / Request" value={formatCost(avgCost)} />
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
