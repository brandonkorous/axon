import { useEffect, useRef, useState } from "react";

interface SandboxBuildProgressProps {
  lines: string[];
  startedAt?: number | null;
}

export function SandboxBuildProgress({ lines, startedAt }: SandboxBuildProgressProps) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const [elapsed, setElapsed] = useState(0);

  // Auto-scroll to bottom on new lines
  useEffect(() => {
    const el = scrollRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [lines]);

  // Elapsed timer
  useEffect(() => {
    if (!startedAt) return;
    const update = () => setElapsed(Math.floor((Date.now() / 1000) - startedAt));
    update();
    const interval = setInterval(update, 1000);
    return () => clearInterval(interval);
  }, [startedAt]);

  const mins = Math.floor(elapsed / 60);
  const secs = elapsed % 60;

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <progress className="progress progress-primary w-full" />
        {startedAt && (
          <span className="text-xs text-base-content/60 ml-3 shrink-0">
            {mins > 0 ? `${mins}m ` : ""}{secs}s
          </span>
        )}
      </div>
      <div
        ref={scrollRef}
        className="bg-base-300 rounded-lg p-3 h-48 overflow-y-auto font-mono text-xs text-base-content/80 leading-relaxed"
        role="log"
        aria-label="Build output"
      >
        {lines.length === 0 ? (
          <span className="text-base-content/40">Waiting for output...</span>
        ) : (
          lines.map((line, i) => (
            <div key={i} className="whitespace-pre-wrap break-all">
              {line}
            </div>
          ))
        )}
      </div>
    </div>
  );
}
