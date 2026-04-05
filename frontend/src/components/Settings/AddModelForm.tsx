import { useState } from "react";
import {
  useModels,
  useModelCatalog,
  useOllamaModels,
  useRegisterModel,
  type RegisteredModel,
  type CatalogProvider,
} from "../../hooks/useModels";

const TIER_BADGE: Record<string, string> = {
  recommended: "badge-primary",
  premium: "badge-secondary",
  budget: "badge-accent",
};

export function AddModelForm({ onClose }: { onClose: () => void }) {
  const { data: modelsData } = useModels();
  const { data: catalog } = useModelCatalog();
  const { data: ollamaData } = useOllamaModels();
  const registerModel = useRegisterModel();
  const [modelId, setModelId] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [modelType, setModelType] = useState<"cloud" | "local">("cloud");
  const [isCustom, setIsCustom] = useState(false);

  const models = modelsData?.registered_models ?? [];
  const ollamaModels: RegisteredModel[] = (ollamaData?.models ?? []).map((m) => ({
    id: m.id,
    provider: "ollama",
    display_name: m.name,
    model_type: "local",
  }));

  const canSave = modelId.trim() && displayName.trim();

  // Build merged provider list: cloud catalog + discovered local models
  const existingIds = new Set(models.map((m) => m.id));
  const ollamaProvider: CatalogProvider | null =
    ollamaModels.length > 0
      ? {
          id: "ollama",
          name: "Local (Ollama)",
          requires_key: false,
          models: ollamaModels
            .filter((m) => !existingIds.has(m.id))
            .map((m) => ({
              id: m.id,
              name: m.display_name || m.id.replace("ollama/", ""),
              description: "Local model",
              tier: "local" as const,
            })),
        }
      : null;
  const allProviders = [
    ...(ollamaProvider && ollamaProvider.models.length > 0 ? [ollamaProvider] : []),
    ...(catalog?.providers || []),
  ];

  const handleCatalogSelect = (value: string) => {
    if (value === "__custom__") {
      setIsCustom(true);
      setModelId("");
      setDisplayName("");
      setModelType("cloud");
      return;
    }
    for (const provider of allProviders) {
      const found = provider.models.find((m) => m.id === value);
      if (found) {
        setIsCustom(false);
        setModelId(found.id);
        setDisplayName(found.name);
        setModelType(provider.id === "ollama" ? "local" : "cloud");
        return;
      }
    }
  };

  const handleSave = async () => {
    if (!canSave) return;
    try {
      await registerModel.mutateAsync({
        id: modelId.trim(),
        display_name: displayName.trim(),
        model_type: modelType,
      });
      onClose();
    } catch {
      // mutation error handled by TQ
    }
  };

  return (
    <div className="border border-neutral/30 rounded p-3 space-y-3 bg-base-100">
      <label className="form-control">
        <span className="label-text text-xs mb-1">Select Model</span>
        <select
          value={isCustom ? "__custom__" : modelId}
          onChange={(e) => handleCatalogSelect(e.target.value)}
          className="select select-sm select-bordered w-full"
        >
          <option value="" disabled>
            Choose a model...
          </option>
          {allProviders.map((provider) => (
            <optgroup key={provider.id} label={provider.name}>
              {provider.models.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.tier !== "local" ? `[${m.tier}] ` : ""}{m.name} — {m.description}
                </option>
              ))}
            </optgroup>
          ))}
          <optgroup label="Other">
            <option value="__custom__">Custom model ID...</option>
          </optgroup>
        </select>
      </label>

      {/* Tier badge for selected model */}
      {!isCustom && modelId && (() => {
        for (const p of allProviders) {
          const m = p.models.find((m) => m.id === modelId);
          if (m && m.tier !== "local") {
            return (
              <span className={`badge badge-sm ${TIER_BADGE[m.tier] ?? ""}`}>
                {m.tier}
              </span>
            );
          }
        }
        return null;
      })()}

      {isCustom && (
        <>
          <label className="form-control">
            <span className="label-text text-xs mb-1">Model ID</span>
            <input
              type="text"
              value={modelId}
              onChange={(e) => setModelId(e.target.value)}
              placeholder="e.g. anthropic/claude-sonnet-4-20250514"
              className="input input-sm input-bordered w-full font-mono"
            />
          </label>
          <label className="form-control">
            <span className="label-text text-xs mb-1">Display Name</span>
            <input
              type="text"
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              placeholder="e.g. Claude Sonnet"
              className="input input-sm input-bordered w-full"
            />
          </label>
          <label className="form-control">
            <span className="label-text text-xs mb-1">Type</span>
            <select
              value={modelType}
              onChange={(e) => setModelType(e.target.value as "cloud" | "local")}
              className="select select-sm select-bordered w-full"
            >
              <option value="cloud">Cloud</option>
              <option value="local">Local</option>
            </select>
          </label>
        </>
      )}

      <div className="flex gap-2">
        <button onClick={handleSave} disabled={!canSave || registerModel.isPending} className="btn btn-primary btn-sm">
          {registerModel.isPending ? <span className="loading loading-spinner loading-xs" /> : "Save"}
        </button>
        <button onClick={onClose} className="btn btn-ghost btn-sm">Cancel</button>
      </div>
    </div>
  );
}

export function OllamaDiscoverButton() {
  const { data: modelsData } = useModels();
  const { data: ollamaData, isLoading: loading, refetch } = useOllamaModels();
  const registerModel = useRegisterModel();

  const models = modelsData?.registered_models ?? [];
  const existingIds = new Set(models.map((m) => m.id));
  const discovered: RegisteredModel[] = (ollamaData?.models ?? [])
    .filter((m) => !existingIds.has(m.id))
    .map((m) => ({
      id: m.id,
      provider: "ollama",
      display_name: m.name,
      model_type: "local",
    }));

  const handleDiscover = () => {
    refetch();
  };

  const handleAdd = async (model: RegisteredModel) => {
    await registerModel.mutateAsync({
      id: model.id,
      display_name: model.display_name,
      model_type: "local",
    });
  };

  return (
    <div className="space-y-2">
      <button onClick={handleDiscover} disabled={loading} className="btn btn-outline btn-sm">
        {loading ? (
          <span className="loading loading-spinner loading-xs" />
        ) : (
          "Discover Ollama Models"
        )}
      </button>
      {discovered.length > 0 && (
        <div className="border border-neutral/30 rounded p-2 space-y-1">
          <p className="text-xs text-base-content/60 mb-1">Available local models:</p>
          {discovered.map((m) => (
            <div key={m.id} className="flex items-center justify-between py-1">
              <span className="text-sm font-mono">{m.display_name}</span>
              <button
                onClick={() => handleAdd(m)}
                disabled={registerModel.isPending}
                className="btn btn-primary btn-xs"
              >
                {registerModel.isPending ? (
                  <span className="loading loading-spinner loading-xs" />
                ) : (
                  "Add"
                )}
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
