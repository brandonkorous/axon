import { useEffect, useState } from "react";
import { useSandboxStore, type SandboxImageInfo } from "../../stores/sandboxStore";
import { SandboxBuildProgress } from "./SandboxBuildProgress";

type Phase = "confirm" | "building" | "complete" | "error";

interface SandboxBuildDialogProps {
  image: SandboxImageInfo;
  onClose: () => void;
}

export function SandboxBuildDialog({ image, onClose }: SandboxBuildDialogProps) {
  const { buildProgress, subscribeBuildProgress, unsubscribeBuildProgress, fetchImages } =
    useSandboxStore();
  const [phase, setPhase] = useState<Phase>("confirm");
  const isReady = image.status === "ready";
  const lines = buildProgress[image.type] || [];

  useEffect(() => {
    return () => unsubscribeBuildProgress(image.type);
  }, [image.type, unsubscribeBuildProgress]);

  const handleBuild = async () => {
    setPhase("building");
    // The WebSocket endpoint triggers the build AND streams progress.
    // Do NOT also call buildImage() — that fires a separate background
    // build without a progress callback, racing the WebSocket build and
    // causing progress lines to never arrive.
    subscribeBuildProgress(image.type, () => {
      fetchImages().then(() => {
        const updated = useSandboxStore.getState().images.find((i) => i.type === image.type);
        setPhase(updated?.status === "error" ? "error" : "complete");
      });
    });
  };

  const handleClose = () => {
    unsubscribeBuildProgress(image.type);
    onClose();
  };

  return (
    <dialog className="modal modal-open" aria-modal="true">
      <div className="modal-box max-w-lg">
        <h3 className="text-lg font-bold">
          {phase === "confirm" && (isReady ? "Rebuild" : "Build")}{" "}
          {phase === "confirm" && `"${image.type}" Image`}
          {phase === "building" && `Building "${image.type}"...`}
          {phase === "complete" && "Build Complete"}
          {phase === "error" && "Build Failed"}
        </h3>

        {phase === "confirm" && (
          <div className="mt-4 space-y-3">
            <p className="text-sm text-base-content/80">{image.description}</p>
            <div className="text-xs text-base-content/60 space-y-1">
              <p>Estimated size: ~{image.estimated_size_mb} MB</p>
              {image.parent_type && <p>Requires: {image.parent_type} image</p>}
              <p>Tools: {image.tools.join(", ") || "none"}</p>
            </div>
            {isReady && (
              <div className="alert alert-warning py-2 px-3">
                <span className="text-xs">
                  This will replace the existing image. Running sandboxes may be affected.
                </span>
              </div>
            )}
          </div>
        )}

        {phase === "building" && (
          <div className="mt-4">
            <SandboxBuildProgress lines={lines} startedAt={image.started_at ?? Date.now() / 1000} />
          </div>
        )}

        {phase === "complete" && (
          <div className="mt-4">
            <div className="alert alert-success py-2 px-3">
              <span className="text-xs">Image built successfully.</span>
            </div>
            <div className="mt-3">
              <SandboxBuildProgress lines={lines} />
            </div>
          </div>
        )}

        {phase === "error" && (
          <div className="mt-4">
            <div className="alert alert-error py-2 px-3">
              <span className="text-xs">
                {image.error || "Build failed. Check logs for details."}
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
              <button onClick={handleBuild} className="btn btn-primary btn-sm">
                {isReady ? "Rebuild" : "Build"}
              </button>
            </>
          )}
          {phase === "building" && (
            <button onClick={handleClose} className="btn btn-ghost btn-sm">
              Close (continues in background)
            </button>
          )}
          {(phase === "complete" || phase === "error") && (
            <button onClick={handleClose} className="btn btn-primary btn-sm">
              Done
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
