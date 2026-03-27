import { useEffect, useState } from "react";
import { useAgentStore } from "../../stores/agentStore";
import { orgApiPath } from "../../stores/orgStore";

interface ModelConfig {
  reasoning: string;
  navigator: string;
  max_tokens: number;
  temperature: number;
}

interface LearningConfig {
  enabled: boolean;
  memory_model: string;
  consolidation_interval: number;
  confidence_decay_days: number;
  max_recall_tokens: number;
}

const MODEL_OPTIONS = [
  { value: "anthropic/claude-sonnet-4-20250514", label: "Claude Sonnet 4" },
  { value: "anthropic/claude-haiku-4-5-20251001", label: "Claude Haiku 4.5" },
  { value: "openai/gpt-4o", label: "GPT-4o" },
  { value: "openai/gpt-4o-mini", label: "GPT-4o Mini" },
  { value: "ollama/llama3:8b", label: "Llama 3 8B (local)" },
  { value: "ollama/llama3:70b", label: "Llama 3 70B (local)" },
  { value: "ollama/mistral", label: "Mistral (local)" },
] as const;

export function ModelsTab() {
  const { agents } = useAgentStore();
  const advisors = agents.filter((a) => a.type !== "external");
  const [selected, setSelected] = useState<string>("");
  const [config, setConfig] = useState<ModelConfig | null>(null);
  const [learning, setLearning] = useState<LearningConfig | null>(null);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (advisors.length > 0 && !selected) {
      setSelected(advisors[0].id);
    }
  }, [advisors, selected]);

  useEffect(() => {
    if (!selected) return;
    setLoading(true);
    Promise.all([
      fetch(orgApiPath(`agents/${selected}/model`)).then((r) => r.ok ? r.json() : null),
      fetch(orgApiPath(`agents/${selected}/learning`)).then((r) => r.ok ? r.json() : null),
    ]).then(([m, l]) => {
      setConfig(m);
      setLearning(l);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, [selected]);

  const handleSave = async () => {
    if (!selected || !config) return;
    setSaving(true);
    const promises: Promise<unknown>[] = [
      fetch(orgApiPath(`agents/${selected}/model`), {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(config),
      }),
    ];
    if (learning) {
      promises.push(
        fetch(orgApiPath(`agents/${selected}/learning`), {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(learning),
        }),
      );
    }
    await Promise.all(promises);
    setSaving(false);
  };

  return (
    <div className="space-y-5">
      <div>
        <h4 className="text-sm font-semibold mb-2">Agent Model Configuration</h4>
        <select
          value={selected}
          onChange={(e) => setSelected(e.target.value)}
          className="select select-sm select-bordered w-full max-w-xs"
        >
          {advisors.map((a) => (
            <option key={a.id} value={a.id}>{a.name}</option>
          ))}
        </select>
      </div>

      {loading ? (
        <div className="flex items-center gap-2 py-4">
          <span className="loading loading-spinner loading-sm" />
          <span className="text-xs text-base-content/60">Loading config...</span>
        </div>
      ) : config ? (
        <>
          <ModelFields config={config} onChange={setConfig} />
          <div className="divider my-0" />
          {learning && <LearningFields config={learning} onChange={setLearning} />}
          <button onClick={handleSave} disabled={saving} className="btn btn-primary btn-sm">
            {saving ? <span className="loading loading-spinner loading-xs" /> : "Save Model Config"}
          </button>
        </>
      ) : (
        <p className="text-xs text-base-content/60">Select an agent to configure its model.</p>
      )}
    </div>
  );
}

function ModelFields({ config, onChange }: { config: ModelConfig; onChange: (c: ModelConfig) => void }) {
  return (
    <div className="space-y-3">
      <label className="form-control">
        <span className="label-text text-xs mb-1">Reasoning model</span>
        <ModelSelect value={config.reasoning} onChange={(v) => onChange({ ...config, reasoning: v })} />
      </label>
      <label className="form-control">
        <span className="label-text text-xs mb-1">Navigator model (memory / search)</span>
        <ModelSelect value={config.navigator} onChange={(v) => onChange({ ...config, navigator: v })} />
      </label>
      <div className="grid grid-cols-2 gap-3">
        <label className="form-control">
          <span className="label-text text-xs mb-1">Temperature ({config.temperature.toFixed(1)})</span>
          <input
            type="range"
            min={0}
            max={1.5}
            step={0.1}
            value={config.temperature}
            onChange={(e) => onChange({ ...config, temperature: parseFloat(e.target.value) })}
            className="range range-sm range-primary"
          />
        </label>
        <label className="form-control">
          <span className="label-text text-xs mb-1">Max tokens</span>
          <input
            type="number"
            value={config.max_tokens}
            onChange={(e) => onChange({ ...config, max_tokens: parseInt(e.target.value) || 4096 })}
            className="input input-sm input-bordered w-full font-mono"
          />
        </label>
      </div>
    </div>
  );
}

function LearningFields({ config, onChange }: { config: LearningConfig; onChange: (c: LearningConfig) => void }) {
  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h4 className="text-sm font-semibold">Learning & Memory</h4>
        <input
          type="checkbox"
          className="toggle toggle-sm toggle-primary"
          checked={config.enabled}
          onChange={(e) => onChange({ ...config, enabled: e.target.checked })}
        />
      </div>
      {config.enabled && (
        <>
          <label className="form-control">
            <span className="label-text text-xs mb-1">Memory model (local LLM)</span>
            <ModelSelect value={config.memory_model} onChange={(v) => onChange({ ...config, memory_model: v })} />
          </label>
          <div className="grid grid-cols-2 gap-3">
            <label className="form-control">
              <span className="label-text text-xs mb-1">Consolidation interval</span>
              <input
                type="number"
                value={config.consolidation_interval}
                onChange={(e) => onChange({ ...config, consolidation_interval: parseInt(e.target.value) || 20 })}
                className="input input-sm input-bordered w-full font-mono"
              />
            </label>
            <label className="form-control">
              <span className="label-text text-xs mb-1">Max recall tokens</span>
              <input
                type="number"
                value={config.max_recall_tokens}
                onChange={(e) => onChange({ ...config, max_recall_tokens: parseInt(e.target.value) || 4000 })}
                className="input input-sm input-bordered w-full font-mono"
              />
            </label>
          </div>
        </>
      )}
    </div>
  );
}

function ModelSelect({ value, onChange }: { value: string; onChange: (v: string) => void }) {
  const isCustom = !MODEL_OPTIONS.some((o) => o.value === value);
  return (
    <div className="flex gap-2">
      <select
        value={isCustom ? "__custom__" : value}
        onChange={(e) => {
          if (e.target.value !== "__custom__") onChange(e.target.value);
        }}
        className="select select-sm select-bordered flex-1"
      >
        {MODEL_OPTIONS.map((o) => (
          <option key={o.value} value={o.value}>{o.label}</option>
        ))}
        <option value="__custom__">Custom...</option>
      </select>
      {isCustom && (
        <input
          type="text"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder="provider/model"
          className="input input-sm input-bordered flex-1 font-mono"
        />
      )}
    </div>
  );
}
