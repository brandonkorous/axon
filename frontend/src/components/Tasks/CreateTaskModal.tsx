import { useEffect, useRef, useState } from "react";
import { useAgentStore } from "../../stores/agentStore";

export interface CreateTaskData {
  title: string;
  description: string;
  assignee: string;
  priority: string;
  start_date?: string;
  due_date?: string;
  estimated_hours?: number | null;
}

export function CreateTaskModal({
  onClose,
  onCreate,
  defaultDate,
}: {
  onClose: () => void;
  onCreate: (data: CreateTaskData) => void;
  defaultDate?: string;
}) {
  const { agents } = useAgentStore();
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [assignee, setAssignee] = useState("");
  const [priority, setPriority] = useState("p2");
  const [startDate, setStartDate] = useState(defaultDate || "");
  const [dueDate, setDueDate] = useState("");
  const [estimatedHours, setEstimatedHours] = useState("");
  const dialogRef = useRef<HTMLDialogElement>(null);

  useEffect(() => {
    dialogRef.current?.showModal();
  }, []);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) return;
    onCreate({
      title,
      description,
      assignee,
      priority,
      start_date: startDate || undefined,
      due_date: dueDate || undefined,
      estimated_hours: estimatedHours ? parseFloat(estimatedHours) : null,
    });
    onClose();
  };

  return (
    <dialog ref={dialogRef} className="modal" onClose={onClose}>
      <div className="modal-box">
        <h3 className="text-lg font-bold mb-4">Create Task</h3>
        <form onSubmit={handleSubmit} className="space-y-3">
          <input
            autoFocus
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Task title"
            aria-label="Task title"
            className="input input-sm w-full"
          />
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Description (optional)"
            aria-label="Task description"
            rows={3}
            className="textarea textarea-sm w-full resize-none"
          />
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
                  <option key={a.id} value={a.id}>{a.name}</option>
                ))}
            </select>
            <select
              value={priority}
              onChange={(e) => setPriority(e.target.value)}
              aria-label="Priority"
              className="select select-sm w-24"
            >
              <option value="p0">P0</option>
              <option value="p1">P1</option>
              <option value="p2">P2</option>
              <option value="p3">P3</option>
            </select>
          </div>
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
          <div className="modal-action">
            <button type="button" onClick={onClose} className="btn btn-ghost btn-sm">
              Cancel
            </button>
            <button type="submit" disabled={!title.trim()} className="btn btn-primary btn-sm">
              Create
            </button>
          </div>
        </form>
      </div>
      <form method="dialog" className="modal-backdrop"><button>close</button></form>
    </dialog>
  );
}
