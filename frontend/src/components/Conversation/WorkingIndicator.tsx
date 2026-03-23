import { useEffect, useRef, useState } from "react";
import { useConversationStore } from "../../stores/conversationStore";

export interface RunningTask {
  path: string;
  title: string;
  agentId: string;
  startedAt: number;
}

interface Props {
  chatId: string;
  tasks: RunningTask[];
  color?: string;
}

function formatElapsed(startedAt: number): string {
  const seconds = Math.floor((Date.now() - startedAt) / 1000);
  if (seconds < 60) return `${seconds}s`;
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m`;
  const hours = Math.floor(minutes / 60);
  return `${hours}h ${minutes % 60}m`;
}

function TaskRow({ chatId, task, color }: { chatId: string; task: RunningTask; color: string }) {
  const [expanded, setExpanded] = useState(false);
  const logRef = useRef<HTMLPreElement>(null);
  const log = useConversationStore((s) => s.taskLogs[chatId]?.[task.path] || "");

  // Auto-scroll log to bottom
  useEffect(() => {
    if (logRef.current && expanded) {
      logRef.current.scrollTop = logRef.current.scrollHeight;
    }
  }, [log, expanded]);

  return (
    <div key={task.path}>
      <div
        className="flex items-center gap-3 px-6 py-2"
        role="status"
        aria-label={`Working on ${task.title}`}
      >
        <span
          className="loading loading-ring loading-sm"
          style={{ color }}
        />
        <span className="text-sm text-neutral-content">
          Working on:{" "}
          <span className="font-medium text-base-content">
            {task.title}
          </span>
        </span>
        <span className="text-xs text-neutral-content/50">
          {formatElapsed(task.startedAt)}
        </span>
        <button
          className="btn btn-ghost btn-xs text-base-content/50 ml-auto"
          onClick={() => setExpanded(!expanded)}
          aria-expanded={expanded}
          aria-label={expanded ? "Hide task log" : "Show task log"}
        >
          {expanded ? "\u25BE Log" : "\u25B8 Log"}
        </button>
      </div>
      {expanded && (
        <pre
          ref={logRef}
          className="mx-6 mb-2 p-3 bg-base-100 border border-neutral rounded text-xs text-base-content/70 font-mono overflow-x-auto max-h-48 overflow-y-auto whitespace-pre-wrap"
        >
          {log || "Waiting for output..."}
        </pre>
      )}
    </div>
  );
}

export function WorkingIndicator({ chatId, tasks, color = "#8B5CF6" }: Props) {
  const [, setTick] = useState(0);

  // Update elapsed time every 10 seconds
  useEffect(() => {
    const interval = setInterval(() => setTick((t) => t + 1), 10_000);
    return () => clearInterval(interval);
  }, []);

  if (tasks.length === 0) return null;

  return (
    <div className="border-t border-neutral/20 bg-base-200/50">
      {tasks.map((task) => (
        <TaskRow key={task.path} chatId={chatId} task={task} color={color} />
      ))}
    </div>
  );
}
