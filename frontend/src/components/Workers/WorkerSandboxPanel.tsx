import { useEffect, useState } from "react";
import { orgApiPath } from "../../stores/orgStore";
import { useSandboxStore } from "../../stores/sandboxStore";

const STATUS_BADGE: Record<string, string> = {
  idle: "badge-ghost",
  building: "badge-warning",
  ready: "badge-success",
  error: "badge-error",
};

interface ResolvedType {
  agent_id: string;
  resolved_type: string;
  required_types: string[];
}

export function WorkerSandboxPanel({ agentId }: { agentId: string }) {
  const { images, fetchImages } = useSandboxStore();
  const [resolved, setResolved] = useState<ResolvedType | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      try {
        const res = await fetch(orgApiPath(`sandbox/${agentId}/resolved-type`));
        if (res.ok) setResolved(await res.json());
      } catch {
        // not available
      }
      await fetchImages();
      setLoading(false);
    };
    load();
  }, [agentId, fetchImages]);

  if (loading) {
    return (
      <div className="flex items-center gap-2 py-2">
        <span className="loading loading-spinner loading-xs text-primary" />
        <span className="text-xs text-base-content/60">Loading sandbox info...</span>
      </div>
    );
  }

  if (!resolved) {
    return (
      <p className="text-xs text-base-content/60">
        No sandbox configuration for this worker.
      </p>
    );
  }

  const resolvedImage = images.find((i) => i.type === resolved.resolved_type);
  const status = resolvedImage?.status || "idle";

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <span className="text-xs text-base-content/60">Sandbox type:</span>
        <span className="badge badge-sm badge-outline">{resolved.resolved_type}</span>
        <span className={`badge badge-xs ${STATUS_BADGE[status]}`}>
          {status}
        </span>
      </div>

      {resolved.required_types.length > 1 && (
        <div>
          <span className="text-xs text-base-content/60">Image chain:</span>
          <div className="flex flex-wrap gap-1 mt-1">
            {resolved.required_types.map((type) => {
              const img = images.find((i) => i.type === type);
              return (
                <span
                  key={type}
                  className={`badge badge-xs ${STATUS_BADGE[img?.status || "idle"]}`}
                >
                  {type}
                </span>
              );
            })}
          </div>
        </div>
      )}

      {resolvedImage && resolvedImage.size_mb != null && (
        <div className="text-xs text-base-content/60">
          Image size: {resolvedImage.size_mb} MB
        </div>
      )}

      {status === "error" && resolvedImage?.error && (
        <div className="alert alert-error py-1.5 px-3">
          <span className="text-xs">{resolvedImage.error}</span>
        </div>
      )}
    </div>
  );
}
