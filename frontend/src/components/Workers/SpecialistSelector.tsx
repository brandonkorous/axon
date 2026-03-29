import { useState } from "react";
import type { CodeSpecialist } from "../../stores/workerStore";
import { CODE_SPECIALISTS } from "../../constants/codeSpecialists";
import { orgApiPath } from "../../stores/orgStore";

interface Props {
  selected: CodeSpecialist;
  codebasePath: string;
  onChange: (specialist: CodeSpecialist) => void;
}

export function SpecialistSelector({ selected, codebasePath, onChange }: Props) {
  const [detecting, setDetecting] = useState(false);

  const handleAutoDetect = async () => {
    if (!codebasePath) return;
    setDetecting(true);
    try {
      const res = await fetch(orgApiPath("workers/specialists/detect"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ codebase_path: codebasePath }),
      });
      if (res.ok) {
        const data = await res.json();
        if (data.specialist) onChange(data.specialist);
      }
    } finally {
      setDetecting(false);
    }
  };

  return (
    <div>
      <div className="flex items-center justify-between">
        <label className="label text-sm font-medium">Specialist</label>
        {codebasePath && (
          <button
            type="button"
            onClick={handleAutoDetect}
            disabled={detecting}
            className="btn btn-ghost btn-xs gap-1 text-primary"
          >
            {detecting ? (
              <span className="loading loading-spinner loading-xs" />
            ) : (
              <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            )}
            Auto-detect
          </button>
        )}
      </div>
      <div className="grid grid-cols-2 gap-2 mt-1">
        {CODE_SPECIALISTS.map((s) => (
          <button
            key={s.id}
            type="button"
            onClick={() => onChange(s.id)}
            className={`flex items-start gap-3 p-3 rounded-lg border text-left transition-colors ${
              selected === s.id
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
              style={{ color: s.color }}
            >
              <path strokeLinecap="round" strokeLinejoin="round" d={s.icon} />
            </svg>
            <div className="min-w-0">
              <div className="text-sm font-medium text-base-content">{s.label}</div>
              <div className="text-xs text-base-content/60 mt-0.5 leading-tight">
                {s.description}
              </div>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}
