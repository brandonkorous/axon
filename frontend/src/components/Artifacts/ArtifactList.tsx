import { useEffect } from "react";
import { useArtifactStore, type ArtifactInfo } from "../../stores/artifactStore";

const TYPE_BADGE: Record<string, { cls: string; label: string }> = {
  report: { cls: "badge-primary", label: "Report" },
  analysis: { cls: "badge-accent", label: "Analysis" },
  brief: { cls: "badge-info", label: "Brief" },
  comparison: { cls: "badge-secondary", label: "Comparison" },
  research: { cls: "badge-ghost", label: "Research" },
};

export function ArtifactList({ onSelect }: { onSelect: (artifact: ArtifactInfo) => void }) {
  const { artifacts, loading, fetchArtifacts } = useArtifactStore();

  useEffect(() => {
    fetchArtifacts();
  }, [fetchArtifacts]);

  if (loading && artifacts.length === 0) {
    return (
      <div className="flex items-center justify-center h-32">
        <span className="loading loading-spinner loading-md text-primary" />
      </div>
    );
  }

  if (artifacts.length === 0) {
    return (
      <div className="text-center text-base-content/60 mt-12">
        <p className="text-sm">No research artifacts yet</p>
        <p className="text-xs mt-1">Ask an agent to research a topic to generate artifacts</p>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {artifacts.map((a) => {
        const badge = TYPE_BADGE[a.type] || TYPE_BADGE.research;
        return (
          <button
            key={a.path}
            onClick={() => onSelect(a)}
            className="card bg-base-300 border border-neutral w-full text-left hover:border-primary/30 transition-colors"
          >
            <div className="card-body p-4">
              <div className="flex items-center gap-2">
                <p className="text-sm font-medium flex-1 truncate">{a.name}</p>
                <span className={`badge badge-xs ${badge.cls}`}>{badge.label}</span>
              </div>
              {a.description && (
                <p className="text-xs text-base-content/60 truncate">{a.description}</p>
              )}
              {a.tags.length > 0 && (
                <div className="flex gap-1 mt-1">
                  {a.tags.slice(0, 4).map((t) => (
                    <span key={t} className="badge badge-xs badge-outline">{t}</span>
                  ))}
                </div>
              )}
            </div>
          </button>
        );
      })}
    </div>
  );
}
