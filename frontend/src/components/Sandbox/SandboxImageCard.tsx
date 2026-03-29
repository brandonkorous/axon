import type { SandboxImageInfo } from "../../stores/sandboxStore";

const STATUS_BADGE: Record<string, string> = {
  idle: "badge-ghost",
  building: "badge-warning",
  ready: "badge-success",
  error: "badge-error",
};

const STATUS_LABEL: Record<string, string> = {
  idle: "Not Built",
  building: "Building",
  ready: "Ready",
  error: "Error",
};

interface SandboxImageCardProps {
  image: SandboxImageInfo;
  onBuild: () => void;
  onRemove: () => void;
}

export function SandboxImageCard({ image, onBuild, onRemove }: SandboxImageCardProps) {
  const isBuilding = image.status === "building";
  const isReady = image.status === "ready";
  const hasError = image.status === "error";

  return (
    <div className="card bg-base-300 border border-neutral">
      <div className="card-body p-4 gap-3">
        {/* Header */}
        <div className="flex items-start justify-between">
          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <h3 className="text-sm font-semibold">{image.type}</h3>
              <span className={`badge badge-xs ${STATUS_BADGE[image.status]}`}>
                {STATUS_LABEL[image.status]}
              </span>
            </div>
            <p className="text-xs text-base-content/60 mt-0.5">{image.description}</p>
          </div>
          {image.parent_type && (
            <span className="badge badge-xs badge-outline shrink-0">
              extends {image.parent_type}
            </span>
          )}
        </div>

        {/* Error message */}
        {hasError && image.error && (
          <div className="alert alert-error py-1.5 px-3">
            <span className="text-xs">{image.error}</span>
          </div>
        )}

        {/* Size info */}
        <div className="flex items-center gap-4 text-xs text-base-content/60">
          {isReady && image.size_mb != null ? (
            <span>{image.size_mb} MB</span>
          ) : (
            <span>~{image.estimated_size_mb} MB estimated</span>
          )}
          {image.agents_using?.length > 0 && (
            <span>{image.agents_using.length} agent{image.agents_using.length !== 1 ? "s" : ""}</span>
          )}
          {image.plugins_requiring?.length > 0 && (
            <span>{image.plugins_requiring.length} plugin{image.plugins_requiring.length !== 1 ? "s" : ""}</span>
          )}
        </div>

        {/* Tools chips */}
        {image.tools?.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {image.tools.slice(0, 6).map((tool) => (
              <span key={tool} className="badge badge-xs badge-ghost font-mono">
                {tool}
              </span>
            ))}
            {image.tools.length > 6 && (
              <span className="badge badge-xs badge-ghost">
                +{image.tools.length - 6} more
              </span>
            )}
          </div>
        )}

        {/* Actions */}
        <div className="flex items-center gap-2 mt-1">
          {!isReady && !isBuilding && (
            <button onClick={onBuild} className="btn btn-primary btn-xs">
              Build
            </button>
          )}
          {isReady && (
            <button onClick={onBuild} className="btn btn-ghost btn-xs">
              Rebuild
            </button>
          )}
          {isBuilding && (
            <span className="flex items-center gap-1.5 text-xs text-warning">
              <span className="loading loading-spinner loading-xs" />
              Building...
            </span>
          )}
          {isReady && (
            <button onClick={onRemove} className="btn btn-ghost btn-xs text-error">
              Remove
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
