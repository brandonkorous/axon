import type { WorkerType } from "../../stores/workerStore";
import { WORKER_TYPES } from "../../constants/workerTypes";

interface Props {
  selected: WorkerType;
  onChange: (type: WorkerType) => void;
}

export function WorkerTypeSelector({ selected, onChange }: Props) {
  return (
    <div>
      <label className="label text-sm font-medium">Worker Type</label>
      <div className="grid grid-cols-2 gap-2 mt-1">
        {WORKER_TYPES.map((t) => (
          <button
            key={t.id}
            type="button"
            onClick={() => onChange(t.id)}
            className={`flex items-start gap-3 p-3 rounded-lg border text-left transition-colors ${
              selected === t.id
                ? "border-primary bg-primary/10"
                : "border-base-300 hover:border-base-content/20"
            }`}
          >
            <svg
              className="w-5 h-5 shrink-0 mt-0.5"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={1.5}
              style={{ color: t.color }}
            >
              <path strokeLinecap="round" strokeLinejoin="round" d={t.icon} />
            </svg>
            <div className="min-w-0">
              <div className="text-sm font-medium text-base-content">{t.label}</div>
              <div className="text-xs text-base-content/60 mt-0.5 leading-tight">
                {t.description}
              </div>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}
