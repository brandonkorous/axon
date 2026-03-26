import { useEffect } from "react";
import { NavLink, useNavigate } from "react-router-dom";
import { useOrgStore } from "../../stores/orgStore";
import { useWorkerStore, WorkerInfo } from "../../stores/workerStore";
import { WORKER_TYPE_MAP } from "../../constants/workerTypes";
import { WorkerControls } from "./WorkerControls";

const STATE_DOT: Record<string, string> = {
  running: "bg-success",
  starting: "bg-success animate-pulse",
  paused: "bg-warning",
  stopping: "bg-warning animate-pulse",
  stopped: "bg-neutral",
};

const STATE_BADGE: Record<string, { cls: string; label: string }> = {
  running: { cls: "badge-success", label: "Running" },
  starting: { cls: "badge-accent", label: "Starting..." },
  paused: { cls: "badge-warning", label: "Paused" },
  stopping: { cls: "badge-warning", label: "Stopping..." },
  stopped: { cls: "badge-ghost", label: "Stopped" },
};

export function WorkerListView() {
  const { workers, loading, fetchWorkers } = useWorkerStore();
  const orgLoading = useOrgStore((s) => s.loading);
  const activeOrgId = useOrgStore((s) => s.activeOrgId);

  useEffect(() => {
    if (orgLoading) return; // Wait for org context before fetching
    fetchWorkers();
    const interval = setInterval(fetchWorkers, 15000);
    return () => clearInterval(interval);
  }, [fetchWorkers, orgLoading, activeOrgId]);

  return (
    <div className="h-full flex flex-col">
      <div className="px-6 py-4 border-b border-neutral flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-base-content">Workers</h1>
          <p className="text-xs text-base-content/60 mt-1">
            External agents connected via local runners
          </p>
        </div>
        <NavLink to="/workers/new" className="btn btn-primary btn-sm">
          + Add Worker
        </NavLink>
      </div>

      <div className="flex-1 overflow-y-auto p-6">
        {loading && workers.length === 0 ? (
          <div className="flex items-center justify-center h-32">
            <span className="loading loading-spinner loading-md text-primary" />
          </div>
        ) : workers.length === 0 ? (
          <EmptyState />
        ) : (
          <div className="max-w-2xl mx-auto space-y-3">
            {workers.map((w) => (
              <WorkerCard key={w.agent_id} worker={w} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function WorkerCard({ worker }: { worker: WorkerInfo }) {
  const navigate = useNavigate();
  const state = worker.process_state || "stopped";
  const dot = STATE_DOT[state] || STATE_DOT.stopped;
  const badge = STATE_BADGE[state] || STATE_BADGE.stopped;
  const typeInfo = WORKER_TYPE_MAP[worker.worker_type || "code"];

  return (
    <div className="card bg-base-300 border border-neutral">
      <div className="card-body p-4 flex-row items-center gap-4">
        <div className={`w-3 h-3 rounded-full shrink-0 ${dot}`} />
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <p className="text-sm font-medium truncate">{worker.name}</p>
            {typeInfo && (
              <span
                className="badge badge-xs badge-outline"
                style={{ borderColor: typeInfo.color, color: typeInfo.color }}
              >
                {typeInfo.label}
              </span>
            )}
          </div>
          <p className="text-xs text-base-content/60 truncate">
            {worker.codebase_path || worker.agent_id}
          </p>
        </div>
        <WorkerControls agentId={worker.agent_id} processState={state} />
        <span className={`badge badge-xs ${badge.cls}`}>
          {badge.label}
        </span>
        <button
          onClick={() => navigate(`/workers/${worker.agent_id}`)}
          className="btn btn-ghost btn-xs"
          title="Details"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
        </button>
      </div>
    </div>
  );
}

function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center h-48 text-center">
      <p className="text-sm text-base-content/60 mb-3">No worker agents configured</p>
      <NavLink to="/workers/new" className="btn btn-primary btn-sm">
        Add Your First Worker
      </NavLink>
    </div>
  );
}
