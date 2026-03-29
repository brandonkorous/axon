import { useEffect } from "react";
import { useAnalyticsStore } from "../../stores/analyticsStore";
import { KpiCards } from "./KpiCards";
import { AgentPerformanceTable } from "./AgentPerformanceTable";
import { ConfidencePanel } from "./ConfidencePanel";
import { ActivityPanel } from "./ActivityPanel";
import { ToolUsagePanel } from "./ToolUsagePanel";
import { DelegationPanel } from "./DelegationPanel";
import { MemoryPanel } from "./MemoryPanel";

export function AnalyticsView() {
  const { data, loading, error, fetch: fetchAnalytics } = useAnalyticsStore();

  useEffect(() => {
    fetchAnalytics();
  }, [fetchAnalytics]);

  if (loading && !data) {
    return (
      <div className="flex items-center justify-center h-full">
        <span className="loading loading-spinner loading-md text-primary" />
      </div>
    );
  }

  return (
    <div className="h-full overflow-y-auto p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-base-content">Analytics</h1>
        <button
          onClick={fetchAnalytics}
          disabled={loading}
          className="btn btn-ghost btn-sm text-base-content/60"
        >
          {loading ? <span className="loading loading-spinner loading-xs" /> : "Refresh"}
        </button>
      </div>

      {error && (
        <div className="flex items-center gap-3 p-3 rounded-lg bg-error/10 border border-error/20 text-error text-sm">
          Failed to load analytics data.
          <button onClick={fetchAnalytics} className="btn btn-ghost btn-xs text-error">
            Retry
          </button>
        </div>
      )}

      {data && (
        <>
          <KpiCards data={data} />
          <AgentPerformanceTable agents={data.agents} />

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <ConfidencePanel agents={data.agents} />
            <MemoryPanel agents={data.agents} />
          </div>

          <ActivityPanel timeline={data.activity_timeline} />

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <ToolUsagePanel toolUsage={data.tool_usage} />
            <DelegationPanel flow={data.delegation_flow} />
          </div>
        </>
      )}
    </div>
  );
}
