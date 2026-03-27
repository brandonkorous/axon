import { useEffect, useRef, useState } from "react";
import { useWorkerStore } from "../../stores/workerStore";

interface WorkerLogPanelProps {
  agentId: string;
}

export function WorkerLogPanel({ agentId }: WorkerLogPanelProps) {
  const { fetchLogs, clearLogs } = useWorkerStore();
  const [lines, setLines] = useState<string[]>([]);
  const [expanded, setExpanded] = useState(false);
  const scrollRef = useRef<HTMLPreElement>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const loadLogs = async () => {
    const result = await fetchLogs(agentId);
    setLines(result);
  };

  const handleClear = async () => {
    const ok = await clearLogs(agentId);
    if (ok) setLines([]);
  };

  useEffect(() => {
    if (!expanded) {
      if (pollRef.current) clearInterval(pollRef.current);
      return;
    }
    loadLogs();
    pollRef.current = setInterval(loadLogs, 5000);
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, [expanded, agentId]);

  // Auto-scroll to bottom when new lines arrive
  useEffect(() => {
    if (scrollRef.current && expanded) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [lines, expanded]);

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2">
        <button
          className="btn btn-ghost btn-xs text-base-content/60"
          onClick={() => setExpanded(!expanded)}
        >
          {expanded ? "\u25BE Hide logs" : "\u25B8 Show logs"}
        </button>

        {expanded && lines.length > 0 && (
          <button
            className="btn btn-ghost btn-xs text-error/60 hover:text-error"
            onClick={handleClear}
          >
            Clear
          </button>
        )}
      </div>

      {expanded && (
        <pre
          ref={scrollRef}
          className="p-3 bg-base-100 border border-neutral rounded text-xs text-base-content/70 font-mono overflow-x-auto max-h-64 overflow-y-auto whitespace-pre-wrap"
        >
          {lines.length > 0
            ? lines.join("\n")
            : "No logs yet"}
        </pre>
      )}
    </div>
  );
}
