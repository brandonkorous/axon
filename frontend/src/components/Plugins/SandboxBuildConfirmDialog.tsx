import { useState } from "react";
import { useSandboxStore, type SandboxImageInfo } from "../../stores/sandboxStore";
import { SandboxBuildProgress } from "../Sandbox/SandboxBuildProgress";

type Phase = "confirm" | "building" | "complete" | "error";

interface SandboxBuildConfirmDialogProps {
  image: SandboxImageInfo;
  pluginName: string;
  onComplete: () => void;
  onCancel: () => void;
}

export function SandboxBuildConfirmDialog({
  image,
  pluginName,
  onComplete,
  onCancel,
}: SandboxBuildConfirmDialogProps) {
  const { buildProgress, subscribeBuildProgress, unsubscribeBuildProgress, fetchImages } =
    useSandboxStore();
  const [phase, setPhase] = useState<Phase>("confirm");
  const lines = buildProgress[image.type] || [];

  const handleBuildAndEnable = async () => {
    setPhase("building");
    // The WebSocket endpoint triggers the build AND streams progress.
    // Do NOT also call buildImage() — that races the WebSocket build.
    subscribeBuildProgress(image.type, () => {
      fetchImages().then(() => {
        const updated = useSandboxStore.getState().images.find((i) => i.type === image.type);
        if (updated?.status === "error") {
          setPhase("error");
        } else {
          setPhase("complete");
          unsubscribeBuildProgress(image.type);
          onComplete();
        }
      });
    });
  };

  const handleClose = () => {
    unsubscribeBuildProgress(image.type);
    onCancel();
  };

  return (
    <dialog className="modal modal-open" aria-modal="true">
      <div className="modal-box max-w-lg">
        <h3 className="text-lg font-bold">
          {phase === "confirm" && "Sandbox Image Required"}
          {phase === "building" && "Building Sandbox Image..."}
          {phase === "complete" && "Build Complete"}
          {phase === "error" && "Build Failed"}
        </h3>

        {phase === "confirm" && (
          <div className="mt-4 space-y-3">
            <p className="text-sm text-base-content/80">
              The plugin <strong>{pluginName}</strong> requires the{" "}
              <code className="text-xs font-mono text-primary">{image.type}</code> sandbox
              image, which hasn't been built yet.
            </p>
            <div className="text-xs text-base-content/60 space-y-1">
              <p>Estimated size: ~{image.estimated_size_mb} MB</p>
              <p>Tools included: {image.tools.join(", ") || "none"}</p>
            </div>
          </div>
        )}

        {phase === "building" && (
          <div className="mt-4">
            <SandboxBuildProgress lines={lines} startedAt={Date.now() / 1000} />
          </div>
        )}

        {phase === "error" && (
          <div className="mt-4">
            <div className="alert alert-error py-2 px-3">
              <span className="text-xs">
                {image.error || "Build failed. The plugin was not enabled."}
              </span>
            </div>
            <div className="mt-3">
              <SandboxBuildProgress lines={lines} />
            </div>
          </div>
        )}

        <div className="modal-action">
          {phase === "confirm" && (
            <>
              <button onClick={handleClose} className="btn btn-ghost btn-sm">
                Cancel
              </button>
              <button onClick={handleBuildAndEnable} className="btn btn-primary btn-sm">
                Build & Enable
              </button>
            </>
          )}
          {phase === "building" && (
            <button onClick={handleClose} className="btn btn-ghost btn-sm">
              Cancel
            </button>
          )}
          {phase === "error" && (
            <button onClick={handleClose} className="btn btn-ghost btn-sm">
              Close
            </button>
          )}
        </div>
      </div>
      <form method="dialog" className="modal-backdrop">
        <button onClick={handleClose}>close</button>
      </form>
    </dialog>
  );
}
