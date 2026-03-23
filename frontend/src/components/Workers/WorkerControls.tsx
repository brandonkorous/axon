import type { ProcessState } from "../../stores/workerStore";
import { useWorkerStore } from "../../stores/workerStore";

interface WorkerControlsProps {
  agentId: string;
  processState: ProcessState;
}

export function WorkerControls({ agentId, processState }: WorkerControlsProps) {
  const { startWorker, stopWorker, pauseWorker, resumeWorker } = useWorkerStore();

  const isTransitional = processState === "starting" || processState === "stopping";
  const isStopped = processState === "stopped";
  const isRunning = processState === "running";
  const isPaused = processState === "paused";

  // Show spinner during transitional states
  if (isTransitional) {
    return (
      <div className="flex items-center gap-1.5" onClick={(e) => e.stopPropagation()}>
        <span className="loading loading-spinner loading-xs text-accent" />
        <span className="text-xs text-base-content/50">
          {processState === "starting" ? "Starting..." : "Stopping..."}
        </span>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-1" onClick={(e) => e.stopPropagation()}>
      {/* Play / Resume */}
      {(isStopped || isPaused) && (
        <button
          className="btn btn-success btn-xs btn-outline"
          onClick={() => isStopped ? startWorker(agentId) : resumeWorker(agentId)}
          title={isStopped ? "Start" : "Resume"}
        >
          <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
            <path d="M6.3 2.8A1.5 1.5 0 004 4.1v11.8a1.5 1.5 0 002.3 1.3l9.2-5.9a1.5 1.5 0 000-2.6L6.3 2.8z" />
          </svg>
        </button>
      )}

      {/* Pause */}
      {isRunning && (
        <button
          className="btn btn-warning btn-xs btn-outline"
          onClick={() => pauseWorker(agentId)}
          title="Pause"
        >
          <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M5.75 3a.75.75 0 01.75.75v12.5a.75.75 0 01-1.5 0V3.75A.75.75 0 015.75 3zm8.5 0a.75.75 0 01.75.75v12.5a.75.75 0 01-1.5 0V3.75a.75.75 0 01.75-.75z" clipRule="evenodd" />
          </svg>
        </button>
      )}

      {/* Stop */}
      {(isRunning || isPaused) && (
        <button
          className="btn btn-error btn-xs btn-outline"
          onClick={() => stopWorker(agentId)}
          title="Stop"
        >
          <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
            <rect x="4" y="4" width="12" height="12" rx="1" />
          </svg>
        </button>
      )}
    </div>
  );
}
