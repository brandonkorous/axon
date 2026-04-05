import { useEffect, useState } from "react";
import { useModels } from "../../hooks/useModels";
import { orgApiPath } from "../../stores/orgStore";

export function AgentModelOverrides({ agentId }: { agentId: string }) {
  const { data } = useModels();
  const models = data?.registered_models ?? [];
  const roles = data?.roles ?? { navigator: "", reasoning: "", memory: "", agent: "" };
  const [overrides, setOverrides] = useState<{ navigator: string; reasoning: string }>({
    navigator: "",
    reasoning: "",
  });
  const [saving, setSaving] = useState(false);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    fetch(orgApiPath(`agents/${agentId}/model`))
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => {
        if (data) setOverrides({ navigator: data.navigator || "", reasoning: data.reasoning || "" });
        setLoaded(true);
      })
      .catch(() => setLoaded(true));
  }, [agentId]);

  const handleSave = async () => {
    setSaving(true);
    await fetch(orgApiPath(`agents/${agentId}/model`), {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(overrides),
    });
    setSaving(false);
  };

  if (!loaded) return null;

  const navDefault = models.find((m) => m.id === roles.navigator);
  const reasonDefault = models.find((m) => m.id === roles.reasoning);

  return (
    <div className="space-y-2">
      <span className="text-xs font-medium">Model Overrides</span>
      <label className="form-control">
        <span className="label-text text-xs mb-1">Navigator</span>
        <select
          value={overrides.navigator}
          onChange={(e) => setOverrides({ ...overrides, navigator: e.target.value })}
          className="select select-xs select-bordered w-full"
        >
          <option value="">
            Use org default{navDefault ? ` (${navDefault.display_name})` : ""}
          </option>
          {models.map((m) => (
            <option key={m.id} value={m.id}>{m.display_name}</option>
          ))}
        </select>
      </label>
      <label className="form-control">
        <span className="label-text text-xs mb-1">Reasoning</span>
        <select
          value={overrides.reasoning}
          onChange={(e) => setOverrides({ ...overrides, reasoning: e.target.value })}
          className="select select-xs select-bordered w-full"
        >
          <option value="">
            Use org default{reasonDefault ? ` (${reasonDefault.display_name})` : ""}
          </option>
          {models.map((m) => (
            <option key={m.id} value={m.id}>{m.display_name}</option>
          ))}
        </select>
      </label>
      <button onClick={handleSave} disabled={saving} className="btn btn-primary btn-xs">
        {saving ? <span className="loading loading-spinner loading-xs" /> : "Save Overrides"}
      </button>
    </div>
  );
}
