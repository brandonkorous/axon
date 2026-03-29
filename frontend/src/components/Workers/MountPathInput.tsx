import { useCallback, useEffect, useRef, useState } from "react";
import { orgApiPath } from "../../stores/orgStore";

interface MountEntry {
  hostPath: string;
  containerPath: string;
}

interface Props {
  mounts: MountEntry[];
  onChange: (mounts: MountEntry[]) => void;
}

type ValidationState = "idle" | "checking" | "valid" | "invalid";

const DEBOUNCE_MS = 300;

export function MountPathInput({ mounts, onChange }: Props) {
  return (
    <div className="space-y-2">
      {mounts.map((m, i) => (
        <MountRow
          key={i}
          entry={m}
          onChange={(updated) => {
            const next = [...mounts];
            next[i] = updated;
            onChange(next);
          }}
          onRemove={() => onChange(mounts.filter((_, j) => j !== i))}
        />
      ))}
      <button
        type="button"
        className="btn btn-ghost btn-sm text-xs"
        onClick={() => onChange([...mounts, { hostPath: "", containerPath: "" }])}
      >
        + Add mount
      </button>
    </div>
  );
}

function MountRow({
  entry,
  onChange,
  onRemove,
}: {
  entry: MountEntry;
  onChange: (e: MountEntry) => void;
  onRemove: () => void;
}) {
  const [state, setState] = useState<ValidationState>("idle");
  const [error, setError] = useState("");
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const validate = useCallback(async (path: string) => {
    if (!path.trim()) {
      setState("idle");
      setError("");
      return;
    }
    setState("checking");
    try {
      const res = await fetch(orgApiPath("sandbox/validate-mount"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ path }),
      });
      const data = await res.json();
      setState(data.valid ? "valid" : "invalid");
      setError(data.error || "");
    } catch {
      setState("invalid");
      setError("Validation request failed");
    }
  }, []);

  const handleHostChange = (value: string) => {
    onChange({ ...entry, hostPath: value });
    if (timerRef.current) clearTimeout(timerRef.current);
    timerRef.current = setTimeout(() => validate(value), DEBOUNCE_MS);
  };

  useEffect(() => {
    return () => { if (timerRef.current) clearTimeout(timerRef.current); };
  }, []);

  return (
    <div className="flex items-start gap-2">
      <div className="flex-1 space-y-1">
        <div className="flex items-center gap-1">
          <input
            value={entry.hostPath}
            onChange={(e) => handleHostChange(e.target.value)}
            placeholder="Host path, e.g. D:\projects\myrepo"
            className={`input input-bordered input-sm flex-1 ${
              state === "valid" ? "input-success" : state === "invalid" ? "input-error" : ""
            }`}
          />
          <StatusIcon state={state} />
        </div>
        {state === "invalid" && error && (
          <p className="text-error text-xs">{error}</p>
        )}
      </div>
      <input
        value={entry.containerPath}
        onChange={(e) => onChange({ ...entry, containerPath: e.target.value })}
        placeholder="/workspace/myrepo"
        className="input input-bordered input-sm w-44"
      />
      <button type="button" className="btn btn-ghost btn-sm" onClick={onRemove}>
        x
      </button>
    </div>
  );
}

function StatusIcon({ state }: { state: ValidationState }) {
  if (state === "checking") return <span className="loading loading-spinner loading-xs" />;
  if (state === "valid") return <span className="text-success text-sm font-bold">ok</span>;
  if (state === "invalid") return <span className="text-error text-sm font-bold">!</span>;
  return null;
}
