import { useEffect, useRef, useState, type DragEvent } from "react";
import { useTaskStore, Task } from "../../stores/taskStore";
import { useAgentStore } from "../../stores/agentStore";
import { PRIORITY_BADGE } from "../../constants/badges";
import { TaskEditModal } from "./TaskEditModal";

const COLUMNS: { key: Task["status"]; label: string; color: string }[] = [
  { key: "pending", label: "Pending", color: "border-neutral-content/30" },
  { key: "in_progress", label: "In Progress", color: "border-info" },
  { key: "blocked", label: "Blocked", color: "border-error" },
  { key: "done", label: "Done", color: "border-success" },
];


function TaskCard({
  task,
  onStatusChange,
  onEdit,
}: {
  task: Task;
  onStatusChange: (path: string, status: string) => void;
  onEdit: (task: Task) => void;
}) {
  const handleDragStart = (e: DragEvent) => {
    e.dataTransfer.setData("text/plain", task.path);
    e.dataTransfer.effectAllowed = "move";
  };

  return (
    <div
      draggable
      onDragStart={handleDragStart}
      className="group card bg-base-300 border border-secondary hover:border-neutral-content/40 transition-colors cursor-grab active:cursor-grabbing"
    >
      <div className="card-body p-3 gap-2">
        <div className="flex items-start justify-between gap-2">
          <h4
            onClick={() => onEdit(task)}
            className="text-sm font-medium text-base-content leading-tight cursor-pointer hover:text-primary transition-colors"
          >
            {task.name}
          </h4>
          <div className="flex items-center gap-1 shrink-0">
            <button
              onClick={(e) => {
                e.stopPropagation();
                onEdit(task);
              }}
              className="btn btn-ghost btn-xs px-1 opacity-0 group-hover:opacity-100 transition-opacity"
              aria-label="Edit task"
            >
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" fill="currentColor" className="size-3">
                <path d="M13.488 2.513a1.75 1.75 0 0 0-2.475 0L3.05 10.476a1.75 1.75 0 0 0-.46.84l-.53 2.65a.75.75 0 0 0 .882.883l2.65-.53a1.75 1.75 0 0 0 .84-.46l7.963-7.963a1.75 1.75 0 0 0 0-2.475ZM11.72 3.22a.25.25 0 0 1 .354 0l.707.707a.25.25 0 0 1 0 .354L5.544 11.518a.25.25 0 0 1-.12.066l-1.545.309.309-1.545a.25.25 0 0 1 .066-.12L11.72 3.22Z" />
              </svg>
            </button>
            <span
              className={`badge badge-soft badge-xs uppercase font-bold ${
                PRIORITY_BADGE[task.priority] || "badge-info"
              }`}
            >
              {task.priority}
            </span>
          </div>
        </div>

        {task.labels?.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {task.labels.map((label) => (
              <span key={label} className="badge badge-soft badge-accent badge-xs">
                {label}
              </span>
            ))}
          </div>
        )}

        <div className="flex items-center justify-between text-xs text-base-content/60">
          <span>{task.assignee || "Unassigned"}</span>
          {task.due_date && <span>{task.due_date}</span>}
        </div>

        <div className="flex gap-1">
          {COLUMNS.filter((c) => c.key !== task.status).map((col) => (
            <button
              key={col.key}
              onClick={(e) => {
                e.stopPropagation();
                onStatusChange(task.path, col.key);
              }}
              className="btn btn-ghost btn-xs text-[10px]"
            >
              {col.label}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

function KanbanColumn({
  column,
  tasks,
  onDrop,
  onStatusChange,
  onEdit,
}: {
  column: (typeof COLUMNS)[number];
  tasks: Task[];
  onDrop: (taskPath: string, status: string) => void;
  onStatusChange: (path: string, status: string) => void;
  onEdit: (task: Task) => void;
}) {
  const [dragOver, setDragOver] = useState(false);

  const handleDragOver = (e: DragEvent) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = "move";
    setDragOver(true);
  };

  const handleDragLeave = () => setDragOver(false);

  const handleDrop = (e: DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const taskPath = e.dataTransfer.getData("text/plain");
    if (taskPath) {
      onDrop(taskPath, column.key);
    }
  };

  return (
    <div
      className="w-64 md:w-72 shrink-0 flex flex-col"
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
      <div className={`flex items-center gap-2 mb-3 pb-2 border-b-2 ${column.color}`}>
        <h3 className="text-sm font-semibold text-base-content/80">{column.label}</h3>
        <span className="badge badge-ghost badge-xs">{tasks.length}</span>
      </div>
      <div
        className={`flex-1 space-y-2 overflow-y-auto rounded-lg p-1 transition-colors ${
          dragOver ? "bg-primary/10 ring-2 ring-primary/30 ring-inset" : ""
        }`}
      >
        {tasks.map((task) => (
          <TaskCard key={task.path} task={task} onStatusChange={onStatusChange} onEdit={onEdit} />
        ))}
        {tasks.length === 0 && (
          <p className={`text-xs text-center py-8 rounded-lg ${
            dragOver ? "text-primary" : "text-base-content/50"
          }`}>
            {dragOver ? "Drop here" : "No tasks"}
          </p>
        )}
      </div>
    </div>
  );
}

function CreateTaskModal({
  onClose,
  onCreate,
}: {
  onClose: () => void;
  onCreate: (data: {
    title: string;
    description: string;
    assignee: string;
    priority: string;
  }) => void;
}) {
  const { agents } = useAgentStore();
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [assignee, setAssignee] = useState("");
  const [priority, setPriority] = useState("p2");
  const dialogRef = useRef<HTMLDialogElement>(null);

  useEffect(() => {
    dialogRef.current?.showModal();
  }, []);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) return;
    onCreate({ title, description, assignee, priority });
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

export function TaskBoardView() {
  const { tasks, loading, error, fetchTasks, updateTask, createTask } =
    useTaskStore();
  const [showCreate, setShowCreate] = useState(false);
  const [editingTask, setEditingTask] = useState<Task | null>(null);

  useEffect(() => {
    fetchTasks();
  }, [fetchTasks]);

  const handleStatusChange = (path: string, status: string) => {
    updateTask(path, { status });
  };

  const handleDrop = (taskPath: string, newStatus: string) => {
    updateTask(taskPath, { status: newStatus });
  };

  const grouped = COLUMNS.map((col) => ({
    ...col,
    tasks: tasks.filter((t) => t.status === col.key),
  }));

  return (
    <div className="h-full flex flex-col">
      <div className="flex items-center justify-between px-6 py-4 border-b border-neutral">
        <div>
          <h1 className="text-xl font-bold text-base-content">Tasks</h1>
          {tasks.length > 0 && (
            <p className="text-xs text-base-content/60 mt-0.5">
              {tasks.length} task{tasks.length !== 1 ? "s" : ""} — drag cards between columns
            </p>
          )}
        </div>
        <button onClick={() => setShowCreate(true)} className="btn btn-primary btn-sm">
          + New Task
        </button>
      </div>

      {loading ? (
        <div className="flex-1 flex items-center justify-center">
          <span className="loading loading-spinner loading-md text-primary" />
        </div>
      ) : error ? (
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <p className="text-sm text-error mb-2">Failed to load tasks</p>
            <button onClick={() => fetchTasks()} className="link link-accent text-xs">
              Try again
            </button>
          </div>
        </div>
      ) : (
        <div className="flex-1 overflow-x-auto p-4">
          <div className="flex gap-4 h-full min-w-max">
            {grouped.map((col) => (
              <KanbanColumn
                key={col.key}
                column={col}
                tasks={col.tasks}
                onDrop={handleDrop}
                onStatusChange={handleStatusChange}
                onEdit={setEditingTask}
              />
            ))}
          </div>
        </div>
      )}

      {showCreate && (
        <CreateTaskModal
          onClose={() => setShowCreate(false)}
          onCreate={(data) => createTask(data)}
        />
      )}

      {editingTask && (
        <TaskEditModal
          task={editingTask}
          onClose={() => setEditingTask(null)}
          onSave={(path, data) => updateTask(path, data)}
        />
      )}
    </div>
  );
}
