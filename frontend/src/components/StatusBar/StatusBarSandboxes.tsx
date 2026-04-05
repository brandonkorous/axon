import { Link } from "react-router-dom";
import {
  useSandboxImages,
  useRunningInstances,
  useBuildImage,
  useRemoveImage,
  useStopInstance,
  type SandboxImageInfo,
  type RunningInstance,
} from "../../hooks/useSandbox";
import { StatusBarPopover } from "./StatusBarPopover";

const STATUS_DOT: Record<string, string> = {
    idle: "bg-neutral/50",
    building: "bg-warning animate-pulse",
    ready: "bg-success",
    error: "bg-error",
};

const STATUS_LABEL: Record<string, string> = {
    idle: "Not built",
    building: "Building",
    ready: "Ready",
    error: "Error",
};

function RunningItem({ instance }: { instance: RunningInstance }) {
    const stopInstance = useStopInstance();

    return (
        <li className="flex flex-row items-center justify-between gap-2 px-3 py-1.5 hover:bg-base-content/5 rounded-lg">
            <div className="flex items-center gap-2 min-w-0 flex-1">
                <span className="w-2 h-2 rounded-full flex-shrink-0 bg-success animate-pulse motion-reduce:animate-none" />
                <span className="text-sm text-base-content truncate">
                    {instance.instance_name || instance.instance_id}
                </span>
                <span className="text-xs text-base-content/40 truncate">
                    {instance.agents.join(", ")}
                </span>
            </div>
            <button
                onClick={() => stopInstance.mutate(instance.instance_id)}
                className="btn btn-error btn-soft btn-xs flex-shrink-0"
            >
                Stop
            </button>
        </li>
    );
}

function ImageItem({ image }: { image: SandboxImageInfo }) {
    const buildImage = useBuildImage();
    const removeImage = useRemoveImage();

    return (
        <li className="flex flex-row items-center justify-between gap-2 px-3 py-1.5 hover:bg-base-content/5 rounded-lg">
            <div className="flex items-center gap-2 min-w-0 flex-1">
                <span
                    className={`w-2 h-2 rounded-full flex-shrink-0 ${STATUS_DOT[image.status] || "bg-neutral/50"}`}
                />
                <span className="text-sm text-base-content truncate">{image.type}</span>
                <span className="text-xs text-base-content/50">
                    {STATUS_LABEL[image.status] || image.status}
                </span>
            </div>

            <div className="flex gap-1 flex-shrink-0">
                {(image.status === "idle" || image.status === "error") && (
                    <button
                        onClick={() => buildImage.mutate(image.type)}
                        className="btn btn-success btn-soft btn-xs"
                    >
                        Build
                    </button>
                )}
                {image.status === "ready" && (
                    <button
                        onClick={() => removeImage.mutate(image.type)}
                        className="btn btn-error btn-soft btn-xs"
                    >
                        Remove
                    </button>
                )}
                {image.status === "building" && (
                    <span className="loading loading-spinner loading-xs text-warning" />
                )}
            </div>
        </li>
    );
}

export function StatusBarSandboxes({ buildingCount }: { buildingCount: number }) {
    const { data: images = [] } = useSandboxImages();
    const { data: runningInstances = [] } = useRunningInstances();

    const runningCount = runningInstances.length;
    const totalCount = runningCount + buildingCount;
    const hasActivity = totalCount > 0;

    return (
        <StatusBarPopover
            label={`${runningCount} running, ${buildingCount} building`}
            trigger={
                <>
                    <span
                        className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${
                            hasActivity ? "bg-success" : "bg-neutral/50"
                        }${runningCount > 0 ? " animate-pulse motion-reduce:animate-none" : ""}`}
                    />
                    <span>{totalCount}</span>
                    <span className="hidden sm:inline">
                        {totalCount === 1 ? "Sandbox" : "Sandboxes"}
                    </span>
                </>
            }
        >
            <div className="flex items-center justify-between px-3 py-2 border-b border-base-content/10">
                <span className="text-xs font-medium text-base-content">Sandboxes</span>
                <Link to="/sandboxes" className="text-xs text-primary hover:underline">
                    View all
                </Link>
            </div>

            <ul className="overflow-y-auto flex-1 p-1 space-y-0.5">
                {/* Running instances */}
                {runningInstances.length > 0 && (
                    <>
                        <li className="px-3 py-1 text-xs font-semibold text-base-content/50">Running</li>
                        {runningInstances.map((inst) => (
                            <RunningItem key={inst.instance_id} instance={inst} />
                        ))}
                    </>
                )}

                {/* Images */}
                {images.length > 0 && (
                    <>
                        <li className="px-3 py-1 text-xs font-semibold text-base-content/50 mt-1">Images</li>
                        {images.map((image) => (
                            <ImageItem key={image.type} image={image} />
                        ))}
                    </>
                )}

                {runningInstances.length === 0 && images.length === 0 && (
                    <li className="px-3 py-3 text-xs text-base-content/50 text-center">
                        No sandbox images configured
                    </li>
                )}
            </ul>
        </StatusBarPopover>
    );
}
