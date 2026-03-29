import type { WorkerInfo } from "../../stores/workerStore";
import { WORKER_TYPE_MAP } from "../../constants/workerTypes";

export function ConfigDisplay({ worker }: { worker: WorkerInfo }) {
  const typeInfo = WORKER_TYPE_MAP[worker.worker_type || "code"];
  return (
    <div className="space-y-3 text-sm">
      <div>
        <span className="text-base-content/60">Type</span>
        <p className="text-xs mt-0.5">{typeInfo?.description || worker.worker_type}</p>
      </div>
      <div>
        <span className="text-base-content/60">
          {worker.worker_type === "code" ? "Codebase" : "Working Directory"}
        </span>
        <p className="font-mono text-xs mt-0.5">{worker.codebase_path || "\u2014"}</p>
      </div>
      <div>
        <span className="text-base-content/60">Accepts from</span>
        <div className="flex flex-wrap gap-1.5 mt-1">
          {worker.accepts_from.length > 0
            ? worker.accepts_from.map((a) => (
                <span key={a} className="badge badge-ghost badge-xs">{a}</span>
              ))
            : <span className="text-xs text-base-content/60">None</span>}
        </div>
      </div>
    </div>
  );
}

export function EditForm({
  name, codebasePath, acceptsFrom, delegators, saving,
  onNameChange, onCodebaseChange, onToggleAgent, onSave, onCancel,
}: {
  name: string;
  codebasePath: string;
  acceptsFrom: string[];
  delegators: { id: string; name: string }[];
  saving: boolean;
  onNameChange: (v: string) => void;
  onCodebaseChange: (v: string) => void;
  onToggleAgent: (id: string) => void;
  onSave: () => void;
  onCancel: () => void;
}) {
  return (
    <div className="space-y-4">
      <div>
        <label className="label text-xs font-medium">Name</label>
        <input value={name} onChange={(e) => onNameChange(e.target.value)} className="input input-sm w-full" />
      </div>
      <div>
        <label className="label text-xs font-medium">Codebase Path</label>
        <input value={codebasePath} onChange={(e) => onCodebaseChange(e.target.value)} className="input input-sm w-full font-mono" />
      </div>
      <div>
        <label className="label text-xs font-medium">Accepts Tasks From</label>
        <div className="flex flex-wrap gap-2 mt-1">
          {delegators.map((a) => (
            <button
              key={a.id}
              type="button"
              onClick={() => onToggleAgent(a.id)}
              className={`badge badge-sm cursor-pointer ${
                acceptsFrom.includes(a.id) ? "badge-accent" : "badge-ghost"
              }`}
            >
              {a.name}
            </button>
          ))}
        </div>
      </div>
      <div className="flex gap-2">
        <button onClick={onCancel} className="btn btn-ghost btn-sm">Cancel</button>
        <button onClick={onSave} disabled={saving} className="btn btn-primary btn-sm">
          {saving ? <span className="loading loading-spinner loading-xs" /> : "Save"}
        </button>
      </div>
    </div>
  );
}
