import { Link } from "react-router-dom";
import { useWorkerStore } from "../../stores/workerStore";
import { WorkerControls } from "../Workers/WorkerControls";
import { StatusBarPopover } from "./StatusBarPopover";

const STATE_LABEL: Record<string, string> = {
    running: "Running",
    starting: "Starting",
    paused: "Paused",
    stopping: "Stopping",
    stopped: "Stopped",
};

const STATE_DOT: Record<string, string> = {
    running: "bg-success",
    starting: "bg-success animate-pulse",
    paused: "bg-warning",
    stopping: "bg-warning animate-pulse",
    stopped: "bg-neutral/50",
};

export function StatusBarWorkers({
    runningCount,
    totalCount,
}: {
    runningCount: number;
    totalCount: number;
}) {
    const workers = useWorkerStore((s) => s.workers);

    return (
        <StatusBarPopover
            label={`${runningCount} of ${totalCount} workers running`}
            trigger={
                <>
                    <span
                        className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${runningCount > 0 ? "bg-success" : "bg-neutral/50"}${runningCount > 0 ? " animate-pulse motion-reduce:animate-none" : ""}`}
                    />
                    <span>{runningCount}</span>
                    <span className="hidden sm:inline">
                        {runningCount === 1 ? "Worker" : "Workers"}
                    </span>
                </>
            }
        >
            <div className="flex flex-row items-center justify-between px-3 py-2 border-b border-base-content/10">
                <span className="text-xs font-medium text-base-content">Workers</span>
                <Link to="/workers" className="text-xs text-primary hover:underline">
                    View all
                </Link>
            </div>

            <ul className="overflow-y-auto flex-1 p-1 space-y-0.5">
                {workers.length === 0 && (
                    <li className="px-3 py-3 text-xs text-base-content/50 text-center">
                        No workers configured
                    </li>
                )}
                {workers.map((worker) => (
                    <li
                        key={worker.agent_id}
                        className="flex flex-row items-center justify-between gap-2 px-3 py-1.5 hover:bg-base-content/5 rounded-lg"
                    >
                        <Link
                            to={`/workers/${worker.agent_id}`}
                            className="flex items-center gap-2 min-w-0 flex-1"
                        >
                            <span
                                className={`w-2 h-2 rounded-full flex-shrink-0 ${STATE_DOT[worker.process_state] || "bg-neutral/50"}`}
                            />
                            <span className="text-sm text-base-content truncate">
                                {worker.name}
                            </span>
                            <span className="text-xs text-base-content/50">
                                {STATE_LABEL[worker.process_state] || worker.process_state}
                            </span>
                        </Link>

                        <WorkerControls
                            agentId={worker.agent_id}
                            processState={worker.process_state}
                        />
                    </li>
                ))}
            </ul>
        </StatusBarPopover>
    );
}
