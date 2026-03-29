import { useEffect, useRef, useState } from "react";
import { Task, TaskResponse } from "../../stores/taskStore";
import { useAgentStore } from "../../stores/agentStore";

const STATUSES = [
  { key: "pending", label: "Pending" },
  { key: "in_progress", label: "In Progress" },
  { key: "blocked", label: "Blocked" },
  { key: "done", label: "Done" },
  { key: "failed", label: "Failed" },
] as const;

const PRIORITIES = ["p0", "p1", "p2", "p3"] as const;

const STATUS_BADGE: Record<string, string> = {
  success: "badge-success",
  error: "badge-error",
};

function formatTimestamp(ts: string): string {
  if (!ts) return "";
  const d = new Date(ts);
  return d.toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

function ResponseThread({ responses }: { responses: TaskResponse[] }) {
  if (!responses?.length) {
    return (
      <div className="text-xs text-base-content/40 italic py-4 text-center">
        No activity yet
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {responses.map((r, i) => (
        <div key={i} className="border border-base-content/10 rounded-lg p-3">
          <div className="flex items-center gap-2 mb-1.5">
            <span className="text-xs font-semibold text-primary">
              {r.from}
            </span>
            {r.status && (
              <span
                className={`badge badge-xs ${STATUS_BADGE[r.status] || "badge-ghost"}`}
              >
                {r.status}
              </span>
            )}
            <span className="text-[10px] text-base-content/40 ml-auto">
              {formatTimestamp(r.timestamp)}
            </span>
          </div>
          <div className="text-sm text-base-content/80 whitespace-pre-wrap break-words max-h-60 overflow-y-auto">
            {r.content}
          </div>
          {r.attachments?.length > 0 && (
            <div className="mt-2 space-y-1">
              {r.attachments.map((a, j) => (
                <div
                  key={j}
                  className="text-xs text-accent flex items-center gap-1"
                >
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    viewBox="0 0 16 16"
                    fill="currentColor"
                    className="size-3"
                  >
                    <path
                      fillRule="evenodd"
                      d="M4 2a2 2 0 0 0-2 2v8a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2V7.414A2 2 0 0 0 13.414 6L10 2.586A2 2 0 0 0 8.586 2H4Zm6 5a1 1 0 1 0-2 0v2.586l-.293-.293a1 1 0 0 0-1.414 1.414l2 2a1 1 0 0 0 1.414 0l2-2a1 1 0 0 0-1.414-1.414L10 9.586V7Z"
                      clipRule="evenodd"
                    />
                  </svg>
                  <span>{a.label || a.path}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

export function TaskEditModal({
  task,
  onClose,
  onSave,
}: {
  task: Task;
  onClose: () => void;
  onSave: (path: string, data: Partial<Task>) => void;
}) {
  const { agents } = useAgentStore();
  const dialogRef = useRef<HTMLDialogElement>(null);
  const [tab, setTab] = useState<"activity" | "edit">(
    task.responses?.length ? "activity" : "edit"
  );

  const [name, setName] = useState(task.name);
  const [status, setStatus] = useState(task.status);
  const [assignee, setAssignee] = useState(task.assignee);
  const [priority, setPriority] = useState(task.priority);
  const [startDate, setStartDate] = useState(task.start_date || "");
  const [dueDate, setDueDate] = useState(task.due_date || "");
  const [estimatedHours, setEstimatedHours] = useState(
    task.estimated_hours?.toString() || ""
  );
  const [labels, setLabels] = useState(task.labels?.join(", ") || "");
  const [body, setBody] = useState(task.body || "");

  useEffect(() => {
    dialogRef.current?.showModal();
  }, []);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;

    const parsedLabels = labels
      .split(",")
      .map((l) => l.trim())
      .filter(Boolean);

    onSave(task.path, {
      name,
      status,
      assignee,
      priority,
      start_date: startDate,
      due_date: dueDate,
      estimated_hours: estimatedHours ? parseFloat(estimatedHours) : null,
      labels: parsedLabels,
      body,
    });
    onClose();
  };

  const responseCount = task.responses?.length || 0;

  return (
    <dialog ref={dialogRef} className="modal" onClose={onClose}>
      <div className="modal-box max-w-2xl max-h-[85vh] flex flex-col">
        {/* Header */}
        <div className="flex items-start justify-between gap-3 mb-3">
          <div className="min-w-0">
            <h3 className="text-lg font-bold text-base-content truncate">
              {task.name}
            </h3>
            <div className="flex items-center gap-2 mt-1 text-xs text-base-content/50">
              {task.assignee && <span>Assigned to {task.assignee}</span>}
              {task.owner && task.owner !== task.assignee && (
                <span>· Owner: {task.owner}</span>
              )}
              {task.created_at && (
                <span>· Created {formatTimestamp(task.created_at)}</span>
              )}
            </div>
          </div>
          <button
            onClick={onClose}
            className="btn btn-ghost btn-sm btn-square shrink-0"
            aria-label="Close"
          >
            ✕
          </button>
        </div>

        {/* Tabs */}
        <div className="tabs tabs-bordered mb-3">
          <button
            className={`tab tab-sm ${tab === "activity" ? "tab-active" : ""}`}
            onClick={() => setTab("activity")}
          >
            Activity
            {responseCount > 0 && (
              <span className="badge badge-xs badge-primary ml-1.5">
                {responseCount}
              </span>
            )}
          </button>
          <button
            className={`tab tab-sm ${tab === "edit" ? "tab-active" : ""}`}
            onClick={() => setTab("edit")}
          >
            Details
          </button>
        </div>

        {/* Tab content */}
        <div className="flex-1 overflow-y-auto">
          {tab === "activity" ? (
            <div className="pr-1">
              {/* Task description */}
              {task.body && (
                <div className="mb-4 pb-3 border-b border-base-content/10">
                  <p className="text-xs font-semibold text-base-content/50 uppercase tracking-wide mb-1">
                    Description
                  </p>
                  <p className="text-sm text-base-content/70 whitespace-pre-wrap">
                    {task.body}
                  </p>
                </div>
              )}
              <ResponseThread responses={task.responses || []} />
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-3 pr-1">
              <input
                autoFocus
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Task name"
                aria-label="Task name"
                className="input input-sm w-full"
              />

              <div className="flex gap-3">
                <select
                  value={status}
                  onChange={(e) =>
                    setStatus(e.target.value as Task["status"])
                  }
                  aria-label="Status"
                  className="select select-sm flex-1"
                >
                  {STATUSES.map((s) => (
                    <option key={s.key} value={s.key}>
                      {s.label}
                    </option>
                  ))}
                </select>
                <select
                  value={priority}
                  onChange={(e) =>
                    setPriority(e.target.value as Task["priority"])
                  }
                  aria-label="Priority"
                  className="select select-sm w-24"
                >
                  {PRIORITIES.map((p) => (
                    <option key={p} value={p}>
                      {p.toUpperCase()}
                    </option>
                  ))}
                </select>
              </div>

              <select
                value={assignee}
                onChange={(e) => setAssignee(e.target.value)}
                aria-label="Assignee"
                className="select select-sm w-full"
              >
                <option value="">Unassigned</option>
                {agents
                  .filter((a) => a.id !== "axon")
                  .map((a) => (
                    <option key={a.id} value={a.id}>
                      {a.name}
                    </option>
                  ))}
              </select>

              <div className="flex gap-3">
                <div className="flex-1">
                  <label className="label text-xs">Start date</label>
                  <input
                    type="date"
                    value={startDate}
                    onChange={(e) => setStartDate(e.target.value)}
                    aria-label="Start date"
                    className="input input-sm w-full"
                  />
                </div>
                <div className="flex-1">
                  <label className="label text-xs">Due date</label>
                  <input
                    type="date"
                    value={dueDate}
                    onChange={(e) => setDueDate(e.target.value)}
                    aria-label="Due date"
                    className="input input-sm w-full"
                  />
                </div>
                <div className="w-24">
                  <label className="label text-xs">Est. hours</label>
                  <input
                    type="number"
                    value={estimatedHours}
                    onChange={(e) => setEstimatedHours(e.target.value)}
                    placeholder="0"
                    step={0.5}
                    min={0}
                    aria-label="Estimated hours"
                    className="input input-sm w-full"
                  />
                </div>
              </div>

              <input
                value={labels}
                onChange={(e) => setLabels(e.target.value)}
                placeholder="Labels (comma-separated)"
                aria-label="Labels"
                className="input input-sm w-full"
              />

              <textarea
                value={body}
                onChange={(e) => setBody(e.target.value)}
                placeholder="Description"
                aria-label="Task description"
                rows={4}
                className="textarea textarea-sm w-full resize-none"
              />

              <div className="modal-action">
                <button
                  type="button"
                  onClick={onClose}
                  className="btn btn-ghost btn-sm"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={!name.trim()}
                  className="btn btn-primary btn-sm"
                >
                  Save
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
      <form method="dialog" className="modal-backdrop">
        <button>close</button>
      </form>
    </dialog>
  );
}
