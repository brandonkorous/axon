import { Link } from "react-router-dom";
import { useSandboxStore, type SandboxImageInfo } from "../../stores/sandboxStore";
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

function SandboxItem({ image }: { image: SandboxImageInfo }) {
    const { buildImage, removeImage } = useSandboxStore();

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
                        onClick={() => buildImage(image.type)}
                        className="btn btn-success btn-soft btn-xs"
                    >
                        Build
                    </button>
                )}
                {image.status === "ready" && (
                    <button
                        onClick={() => removeImage(image.type)}
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
    const images = useSandboxStore((s) => s.images);

    return (
        <StatusBarPopover
            label={`${buildingCount} sandbox builds in progress`}
            trigger={
                <>
                    <span
                        className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${buildingCount > 0 ? "bg-warning" : "bg-neutral/50"}${buildingCount > 0 ? " animate-pulse motion-reduce:animate-none" : ""}`}
                    />
                    <span>{buildingCount}</span>
                    <span className="hidden sm:inline">
                        {buildingCount === 1 ? "Sandbox" : "Sandboxes"}
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
                {images.length === 0 && (
                    <li className="px-3 py-3 text-xs text-base-content/50 text-center">
                        No sandbox images configured
                    </li>
                )}
                {images.map((image) => (
                    <SandboxItem key={image.type} image={image} />
                ))}
            </ul>
        </StatusBarPopover>
    );
}
