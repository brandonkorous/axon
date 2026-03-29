import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useWorkerStore, type ProcessState, type WorkerType, type CodeSpecialist } from "../../stores/workerStore";
import { useAgentStore } from "../../stores/agentStore";
import { WorkerTypeSelector } from "./WorkerTypeSelector";
import { WorkerTypeConfig } from "./WorkerTypeConfig";
import { SpecialistSelector } from "./SpecialistSelector";
import { MountPathInput } from "./MountPathInput";
import { WorkerRepoSelect } from "./WorkerRepoSelect";

type Step = "form" | "connect";

export function WorkerSetupView() {
  const navigate = useNavigate();
  const { creating, createdAgentId, createWorker, startWorker, fetchWorker, reset } = useWorkerStore();
  const { agents, fetchAgents } = useAgentStore();
  const [step, setStep] = useState<Step>("form");
  const [processState, setProcessState] = useState<ProcessState>("stopped");
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const [name, setName] = useState("");
  const [workerType, setWorkerType] = useState<WorkerType>("code");
  const [specialist, setSpecialist] = useState<CodeSpecialist>("general");
  const [codebasePath, setCodebasePath] = useState("");
  const [typeConfig, setTypeConfig] = useState<Record<string, string>>({});
  const [acceptsFrom, setAcceptsFrom] = useState<string[]>(["axon"]);
  const [sandboxEnabled, setSandboxEnabled] = useState(false);
  const [extraMounts, setExtraMounts] = useState<{ hostPath: string; containerPath: string }[]>([]);
  const [repoIds, setRepoIds] = useState<string[]>([]);

  useEffect(() => {
    reset();
    return () => { if (pollRef.current) clearInterval(pollRef.current); };
  }, [reset]);

  useEffect(() => {
    if (step !== "connect" || !createdAgentId) return;
    const poll = async () => {
      const w = await fetchWorker(createdAgentId);
      if (w) setProcessState(w.process_state || "stopped");
    };
    poll();
    pollRef.current = setInterval(poll, 5000);
    return () => { if (pollRef.current) clearInterval(pollRef.current); };
  }, [step, createdAgentId, fetchWorker]);

  const handleTypeConfigChange = (key: string, value: string) => {
    setTypeConfig((prev) => ({ ...prev, [key]: value }));
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;
    const ok = await createWorker({
      name,
      worker_type: workerType,
      specialist: workerType === "code" ? specialist : undefined,
      codebase_path: codebasePath,
      accepts_from: acceptsFrom,
      type_config: Object.keys(typeConfig).length > 0 ? typeConfig : undefined,
      sandbox: {
        enabled: sandboxEnabled,
        extra_mounts: sandboxEnabled
          ? extraMounts
              .filter((m) => m.hostPath && m.containerPath)
              .map((m) => `${m.hostPath}:${m.containerPath}`)
          : undefined,
        repo_ids: sandboxEnabled && repoIds.length > 0 ? repoIds : undefined,
      },
    });
    if (ok) {
      fetchAgents();
      setStep("connect");
    }
  };

  const handleStart = async () => {
    if (!createdAgentId) return;
    const ok = await startWorker(createdAgentId);
    if (ok) setProcessState("running");
  };

  const toggleAgent = (id: string) => {
    setAcceptsFrom((prev) =>
      prev.includes(id) ? prev.filter((a) => a !== id) : [...prev, id],
    );
  };

  const delegators = agents.filter((a) => a.id !== "huddle");

  return (
    <div className="h-full flex flex-col">
      <div className="px-6 py-4 border-b border-neutral">
        <h1 className="text-xl font-bold text-base-content">Add Worker Agent</h1>
        <p className="text-xs text-base-content/60 mt-1">
          Connect a local runner to execute tasks
        </p>
      </div>

      <div className="flex-1 overflow-y-auto p-6">
        <div className="max-w-xl mx-auto space-y-6">
          {step === "form" && (
            <SetupForm
              name={name}
              workerType={workerType}
              specialist={specialist}
              codebasePath={codebasePath}
              typeConfig={typeConfig}
              acceptsFrom={acceptsFrom}
              sandboxEnabled={sandboxEnabled}
              delegators={delegators}
              creating={creating}
              onNameChange={setName}
              onWorkerTypeChange={setWorkerType}
              onSpecialistChange={setSpecialist}
              onCodebaseChange={setCodebasePath}
              onTypeConfigChange={handleTypeConfigChange}
              onToggleAgent={toggleAgent}
              onSandboxChange={setSandboxEnabled}
              extraMounts={extraMounts}
              onExtraMountsChange={setExtraMounts}
              repoIds={repoIds}
              onRepoIdsChange={setRepoIds}
              onSubmit={handleCreate}
            />
          )}

          {step === "connect" && createdAgentId && (
            <ConnectPanel
              processState={processState}
              onStart={handleStart}
              onGoToDetail={() => navigate(`/workers/${createdAgentId}`)}
            />
          )}
        </div>
      </div>
    </div>
  );
}

function SetupForm({
  name, workerType, specialist, codebasePath, typeConfig, acceptsFrom, sandboxEnabled, delegators, creating,
  extraMounts, repoIds, onNameChange, onWorkerTypeChange, onSpecialistChange, onCodebaseChange, onTypeConfigChange,
  onToggleAgent, onSandboxChange, onExtraMountsChange, onRepoIdsChange, onSubmit,
}: {
  name: string;
  workerType: WorkerType;
  specialist: CodeSpecialist;
  codebasePath: string;
  typeConfig: Record<string, string>;
  acceptsFrom: string[];
  sandboxEnabled: boolean;
  delegators: { id: string; name: string }[];
  creating: boolean;
  extraMounts: { hostPath: string; containerPath: string }[];
  repoIds: string[];
  onNameChange: (v: string) => void;
  onWorkerTypeChange: (v: WorkerType) => void;
  onSpecialistChange: (v: CodeSpecialist) => void;
  onCodebaseChange: (v: string) => void;
  onTypeConfigChange: (key: string, value: string) => void;
  onToggleAgent: (id: string) => void;
  onSandboxChange: (v: boolean) => void;
  onExtraMountsChange: (v: { hostPath: string; containerPath: string }[]) => void;
  onRepoIdsChange: (v: string[]) => void;
  onSubmit: (e: React.FormEvent) => void;
}) {
  return (
    <form onSubmit={onSubmit} className="space-y-5">
      <div>
        <label className="label text-sm font-medium">Name</label>
        <input
          autoFocus
          value={name}
          onChange={(e) => onNameChange(e.target.value)}
          placeholder="e.g. Enterprise Architect"
          className="input input-sm w-full"
        />
      </div>

      <WorkerTypeSelector selected={workerType} onChange={onWorkerTypeChange} />

      <WorkerTypeConfig
        type={workerType}
        codebasePath={codebasePath}
        typeConfig={typeConfig}
        onCodebaseChange={onCodebaseChange}
        onTypeConfigChange={onTypeConfigChange}
      />

      {workerType === "code" && (
        <SpecialistSelector
          selected={specialist}
          codebasePath={codebasePath}
          onChange={onSpecialistChange}
        />
      )}

      <div>
        <label className="label text-sm font-medium">Accepts Tasks From</label>
        <div className="flex flex-wrap gap-2 mt-1">
          {delegators.map((a) => (
            <button
              key={a.id}
              type="button"
              onClick={() => onToggleAgent(a.id)}
              className={`badge badge-sm cursor-pointer ${
                acceptsFrom.includes(a.id) ? "badge-accent" : "badge-ghost"
              }`}
            >
              {a.name}
            </button>
          ))}
        </div>
        <p className="text-xs text-base-content/60 mt-1">
          Which agents can delegate tasks to this worker
        </p>
      </div>

      <div>
        <label className="label text-sm font-medium">Isolation</label>
        <label className="flex items-center gap-3 cursor-pointer mt-1">
          <input
            type="checkbox"
            className="toggle toggle-sm toggle-info"
            checked={sandboxEnabled}
            onChange={(e) => onSandboxChange(e.target.checked)}
          />
          <div>
            <span className="text-sm">Run in sandbox</span>
            <p className="text-xs text-base-content/60">
              Execute in an isolated Docker container with resource limits
            </p>
          </div>
        </label>
      </div>

      {sandboxEnabled && (
        <div>
          <label className="label text-sm font-medium">Host Mounts</label>
          <p className="text-xs text-base-content/60 mb-2">
            Map host directories into the sandbox container
          </p>
          <MountPathInput mounts={extraMounts} onChange={onExtraMountsChange} />
        </div>
      )}

      {sandboxEnabled && (
        <div>
          <label className="label text-sm font-medium">Repositories</label>
          <p className="text-xs text-base-content/60 mb-2">
            Git repositories to clone into the sandbox on start
          </p>
          <WorkerRepoSelect selectedRepoIds={repoIds} onChange={onRepoIdsChange} />
        </div>
      )}

      <button
        type="submit"
        disabled={!name.trim() || creating}
        className="btn btn-primary btn-sm w-full"
      >
        {creating ? (
          <span className="loading loading-spinner loading-xs" />
        ) : (
          "Create Worker"
        )}
      </button>
    </form>
  );
}

function ConnectPanel({
  processState, onStart, onGoToDetail,
}: {
  processState: ProcessState;
  onStart: () => void;
  onGoToDetail: () => void;
}) {
  const [starting, setStarting] = useState(false);
  const isRunning = processState === "running";

  const handleStart = async () => {
    setStarting(true);
    await onStart();
    setStarting(false);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <div className={`w-3 h-3 rounded-full ${
          isRunning ? "bg-success" : "bg-neutral animate-pulse"
        }`} />
        <span className="text-sm font-medium">
          {isRunning ? "Running" : "Ready to start"}
        </span>
      </div>

      {!isRunning && (
        <button
          className="btn btn-success btn-sm w-full"
          onClick={handleStart}
          disabled={starting}
        >
          {starting ? (
            <span className="loading loading-spinner loading-xs" />
          ) : (
            "Start Worker"
          )}
        </button>
      )}

      {isRunning && (
        <div className="alert alert-success text-sm">
          Worker is running. Agents can now delegate tasks to it.
        </div>
      )}

      <button className="btn btn-ghost btn-sm w-full" onClick={onGoToDetail}>
        Go to Worker Details
      </button>
    </div>
  );
}
