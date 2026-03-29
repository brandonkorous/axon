import { useEffect, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useOrgStore } from "../../stores/orgStore";
import { useWorkerStore, WorkerActivity, WorkerInfo, ProcessState } from "../../stores/workerStore";
import { useAgentStore } from "../../stores/agentStore";
import { WORKER_TYPE_MAP } from "../../constants/workerTypes";
import { WorkerControls } from "./WorkerControls";
import { WorkerLogPanel } from "./WorkerLogPanel";
import { WorkerSandboxPanel } from "./WorkerSandboxPanel";
import { ConfigDisplay, EditForm } from "./WorkerConfigSection";

const ACTIVITY_LABEL: Record<string, string> = {
  generating_plan: "Generating plan",
  awaiting_approval: "Awaiting approval",
  executing: "Executing",
};

const STATE_DOT: Record<string, string> = {
  running: "bg-success",
  starting: "bg-success animate-pulse",
  paused: "bg-warning",
  stopping: "bg-warning animate-pulse",
  stopped: "bg-neutral animate-pulse",
};

const STATE_LABEL: Record<string, string> = {
  running: "Running",
  starting: "Starting...",
  paused: "Paused",
  stopping: "Stopping...",
  stopped: "Stopped",
};

export function WorkerDetailView() {
  const { agentId } = useParams<{ agentId: string }>();
  const navigate = useNavigate();
  const { fetchWorker, updateWorker, deleteWorker, workers } = useWorkerStore();
  const { agents } = useAgentStore();
  const orgLoading = useOrgStore((s) => s.loading);

  const [worker, setWorker] = useState<WorkerInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);

  const [name, setName] = useState("");
  const [codebasePath, setCodebasePath] = useState("");
  const [acceptsFrom, setAcceptsFrom] = useState<string[]>([]);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const loadWorker = async () => {
    if (!agentId) return;
    const w = await fetchWorker(agentId);
    if (w) {
      setWorker(w);
      if (!editing) {
        setName(w.name);
        setCodebasePath(w.codebase_path);
        setAcceptsFrom(w.accepts_from);
      }
    }
  };

  useEffect(() => {
    if (orgLoading) return;
    setLoading(true);
    loadWorker().then(() => setLoading(false));
    pollRef.current = setInterval(loadWorker, 10000);
    return () => { if (pollRef.current) clearInterval(pollRef.current); };
  }, [agentId, orgLoading]);

  const handleSave = async () => {
    if (!agentId) return;
    setSaving(true);
    const ok = await updateWorker(agentId, {
      name: name !== worker?.name ? name : undefined,
      codebase_path: codebasePath !== worker?.codebase_path ? codebasePath : undefined,
      accepts_from: JSON.stringify(acceptsFrom) !== JSON.stringify(worker?.accepts_from) ? acceptsFrom : undefined,
    });
    if (ok) {
      const updated = await fetchWorker(agentId);
      setWorker(updated);
      setEditing(false);
    }
    setSaving(false);
  };

  const handleDelete = async () => {
    if (!agentId) return;
    const ok = await deleteWorker(agentId);
    if (ok) navigate("/workers");
  };

  const toggleAgent = (id: string) => {
    setAcceptsFrom((prev) =>
      prev.includes(id) ? prev.filter((a) => a !== id) : [...prev, id],
    );
  };

  if (loading) {
    return (
      <div className="h-full flex items-center justify-center">
        <span className="loading loading-spinner loading-md text-primary" />
      </div>
    );
  }

  if (!worker) {
    return (
      <div className="h-full flex items-center justify-center">
        <p className="text-sm text-error">Worker not found</p>
      </div>
    );
  }

  const storeWorker = workers.find((w) => w.agent_id === agentId);
  const state: ProcessState = storeWorker?.process_state || worker.process_state || "stopped";
  const activity: WorkerActivity | null = storeWorker?.activity || worker.activity || null;
  const delegators = agents.filter((a) => a.id !== "huddle");

  return (
    <div className="h-full flex flex-col">
      <div className="px-6 py-4 border-b border-neutral flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold text-base-content">{worker.name}</h1>
            {WORKER_TYPE_MAP[worker.worker_type || "code"] && (() => {
              const t = WORKER_TYPE_MAP[worker.worker_type || "code"];
              return <span className="badge badge-sm badge-outline" style={{ borderColor: t.color, color: t.color }}>{t.label}</span>;
            })()}
          </div>
          {activity && activity.phase !== "idle" ? (
            <p className="text-xs text-info mt-1 flex items-center gap-1.5">
              <span className="loading loading-dots loading-xs" />
              <span>
                {ACTIVITY_LABEL[activity.phase] || activity.phase}
                {activity.task_name ? `: ${activity.task_name}` : ""}
              </span>
            </p>
          ) : (
            <p className="text-xs text-base-content/60 mt-1">{worker.agent_id}</p>
          )}
        </div>
        <div className="flex items-center gap-3">
          <WorkerControls agentId={worker.agent_id} processState={state} />
          <div className="flex items-center gap-2">
            <div className={`w-2.5 h-2.5 rounded-full ${STATE_DOT[state] || STATE_DOT.stopped}`} />
            <span className="text-xs text-base-content/60">{STATE_LABEL[state] || "Stopped"}</span>
          </div>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-6">
        <div className="max-w-xl mx-auto space-y-6">
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-semibold">Configuration</h2>
              {!editing && (
                <button onClick={() => setEditing(true)} className="btn btn-ghost btn-xs">Edit</button>
              )}
            </div>
            {editing ? (
              <EditForm
                name={name} codebasePath={codebasePath} acceptsFrom={acceptsFrom}
                delegators={delegators} saving={saving}
                onNameChange={setName} onCodebaseChange={setCodebasePath}
                onToggleAgent={toggleAgent} onSave={handleSave}
                onCancel={() => { setEditing(false); setName(worker.name); setCodebasePath(worker.codebase_path); setAcceptsFrom(worker.accepts_from); }}
              />
            ) : (
              <ConfigDisplay worker={worker} />
            )}
          </div>

          {worker.sandboxed && (
            <div className="space-y-3">
              <h2 className="text-sm font-semibold">Sandbox</h2>
              <WorkerSandboxPanel agentId={worker.agent_id} />
            </div>
          )}

          <div className="space-y-3">
            <h2 className="text-sm font-semibold">Runner Logs</h2>
            <WorkerLogPanel agentId={worker.agent_id} />
          </div>

          <div className="border border-error/30 rounded-lg p-4 space-y-3">
            <h2 className="text-sm font-semibold text-error">Danger Zone</h2>
            <p className="text-xs text-base-content/60">
              Stop the runner and remove this worker from the registry. Vault files are preserved.
            </p>
            <button onClick={handleDelete} className="btn btn-error btn-sm btn-outline">Remove Worker</button>
          </div>
        </div>
      </div>
    </div>
  );
}
