import { useEffect, useRef, useState } from "react";
import { Task } from "../../stores/taskStore";
import { useAgentStore } from "../../stores/agentStore";

const STATUSES = [
  { key: "pending", label: "Pending" },
  { key: "in_progress", label: "In Progress" },
  { key: "blocked", label: "Blocked" },
  { key: "done", label: "Done" },
] as const;

const PRIORITIES = ["p0", "p1", "p2", "p3"] as const;

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

  const [name, setName] = useState(task.name);
  const [status, setStatus] = useState(task.status);
  const [assignee, setAssignee] = useState(task.assignee);
  const [priority, setPriority] = useState(task.priority);
  const [dueDate, setDueDate] = useState(task.due_date || "");
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
      due_date: dueDate,
      labels: parsedLabels,
      body,
    });
    onClose();
  };

  return (
    <dialog ref={dialogRef} className="modal" onClose={onClose}>
      <div className="modal-box max-w-lg">
        <h3 className="text-lg font-bold mb-4">Edit Task</h3>
        <form onSubmit={handleSubmit} className="space-y-3">
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
              onChange={(e) => setStatus(e.target.value as Task["status"])}
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
              onChange={(e) => setPriority(e.target.value as Task["priority"])}
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

          <div className="flex gap-3">
            <select
              value={assignee}
              onChange={(e) => setAssignee(e.target.value)}
              aria-label="Assignee"
              className="select select-sm flex-1"
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
            <input
              type="date"
              value={dueDate}
              onChange={(e) => setDueDate(e.target.value)}
              aria-label="Due date"
              className="input input-sm flex-1"
            />
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
      </div>
      <form method="dialog" className="modal-backdrop">
        <button>close</button>
      </form>
    </dialog>
  );
}
