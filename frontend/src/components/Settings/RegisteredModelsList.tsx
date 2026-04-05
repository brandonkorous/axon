import { useState } from "react";
import { useModels, useUnregisterModel, type RegisteredModel } from "../../hooks/useModels";

export function RegisteredModelsList() {
  const { data } = useModels();
  const unregisterModel = useUnregisterModel();
  const models = data?.registered_models ?? [];
  const [confirmId, setConfirmId] = useState<string | null>(null);

  const handleRemove = async (modelId: string) => {
    await unregisterModel.mutateAsync(modelId);
    setConfirmId(null);
  };

  if (models.length === 0) {
    return (
      <p className="text-xs text-base-content/60 py-2">
        No models registered yet. Add a model or discover local Ollama models.
      </p>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="table table-xs w-full">
        <thead>
          <tr className="text-xs text-base-content/60">
            <th>Display Name</th>
            <th>Model ID</th>
            <th>Type</th>
            <th>Provider</th>
            <th />
          </tr>
        </thead>
        <tbody>
          {models.map((m) => (
            <ModelRow
              key={m.id}
              model={m}
              confirming={confirmId === m.id}
              removing={unregisterModel.isPending && confirmId === m.id}
              onConfirm={() => setConfirmId(m.id)}
              onCancel={() => setConfirmId(null)}
              onRemove={() => handleRemove(m.id)}
            />
          ))}
        </tbody>
      </table>
    </div>
  );
}

function ModelRow({
  model,
  confirming,
  removing,
  onConfirm,
  onCancel,
  onRemove,
}: {
  model: RegisteredModel;
  confirming: boolean;
  removing: boolean;
  onConfirm: () => void;
  onCancel: () => void;
  onRemove: () => void;
}) {
  return (
    <tr>
      <td className="font-medium">{model.display_name}</td>
      <td className="font-mono text-base-content/70">{model.id}</td>
      <td>
        <span
          className={`badge badge-xs ${
            model.model_type === "local" ? "badge-accent" : "badge-info"
          }`}
        >
          {model.model_type}
        </span>
      </td>
      <td className="text-base-content/70">{model.provider}</td>
      <td className="text-right">
        {confirming ? (
          <span className="inline-flex gap-1">
            <button
              onClick={onRemove}
              disabled={removing}
              className="btn btn-error btn-xs"
            >
              {removing ? (
                <span className="loading loading-spinner loading-xs" />
              ) : (
                "Confirm"
              )}
            </button>
            <button onClick={onCancel} className="btn btn-ghost btn-xs">
              Cancel
            </button>
          </span>
        ) : (
          <button onClick={onConfirm} className="btn btn-ghost btn-xs text-error">
            Remove
          </button>
        )}
      </td>
    </tr>
  );
}
