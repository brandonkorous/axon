import { useMemo, useState, type DragEvent } from "react";
import { useTasks, useCreateTask, useUpdateTask, type Task } from "../../hooks/useTasks";
import { useAgents } from "../../hooks/useAgents";
import { PRIORITY_BADGE } from "../../constants/badges";
import { TaskEditModal } from "./TaskEditModal";
import { CreateTaskModal } from "./CreateTaskModal";
import { TaskFilterBar, TaskFilters, SortKey } from "./TaskFilterBar";

const COLUMNS: { key: Task["status"]; label: string; color: string }[] = [
    { key: "pending", label: "Pending", color: "border-neutral-content/30" },
    { key: "in_progress", label: "In Progress", color: "border-info" },
    { key: "blocked", label: "Blocked", color: "border-error" },
    { key: "done", label: "Done", color: "border-success" },
    { key: "accepted", label: "Accepted", color: "border-primary" },
];

const CLOSEABLE_STATUSES = new Set(["done", "accepted"]);


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
            className="group card bg-base-200 border border-secondary hover:border-neutral-content/40 transition-colors cursor-grab active:cursor-grabbing"
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
                            className={`badge badge-soft badge-xs uppercase font-bold ${PRIORITY_BADGE[task.priority] || "badge-info"
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
                    <div className="flex items-center gap-2">
                        <span>{task.assignee || "Unassigned"}</span>
                        {task.responses?.length > 0 && (
                            <span className="badge badge-ghost badge-xs" title={`${task.responses.length} response(s)`}>
                                {task.responses.length} {task.responses.length === 1 ? "reply" : "replies"}
                            </span>
                        )}
                    </div>
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
                    {CLOSEABLE_STATUSES.has(task.status) && (
                        <button
                            onClick={(e) => {
                                e.stopPropagation();
                                onStatusChange(task.path, "closed");
                            }}
                            className="btn btn-ghost btn-xs text-[10px] ml-auto text-base-content/40 hover:text-base-content"
                            title="Close — remove from board"
                        >
                            Close
                        </button>
                    )}
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
                className={`flex-1 space-y-2 overflow-y-auto rounded-lg p-1 transition-colors ${dragOver ? "bg-primary/10 ring-2 ring-primary/30 ring-inset" : ""
                    }`}
            >
                {tasks.map((task) => (
                    <TaskCard key={task.path} task={task} onStatusChange={onStatusChange} onEdit={onEdit} />
                ))}
                {tasks.length === 0 && (
                    <p className={`text-xs text-center py-8 rounded-lg ${dragOver ? "text-primary" : "text-base-content/50"
                        }`}>
                        {dragOver ? "Drop here" : "No tasks"}
                    </p>
                )}
            </div>
        </div>
    );
}

function ClosedTasksList({
    tasks,
    agents,
    expanded,
    onToggle,
    onReopen,
    onEdit,
}: {
    tasks: Task[];
    agents: { id: string; name: string }[];
    expanded: boolean;
    onToggle: () => void;
    onReopen: (path: string) => void;
    onEdit: (task: Task) => void;
}) {
    const agentName = (id: string) =>
        agents.find((a) => a.id === id)?.name || id || "Unassigned";

    return (
        <div className="border-t border-neutral px-6 py-3">
            <button
                onClick={onToggle}
                className="flex items-center gap-2 text-sm font-semibold text-base-content/60 hover:text-base-content transition-colors w-full"
            >
                <svg
                    xmlns="http://www.w3.org/2000/svg"
                    viewBox="0 0 16 16"
                    fill="currentColor"
                    className={`size-3 transition-transform ${expanded ? "rotate-90" : ""}`}
                >
                    <path
                        fillRule="evenodd"
                        d="M6.22 4.22a.75.75 0 0 1 1.06 0l3.25 3.25a.75.75 0 0 1 0 1.06l-3.25 3.25a.75.75 0 0 1-1.06-1.06L8.94 8 6.22 5.28a.75.75 0 0 1 0-1.06Z"
                        clipRule="evenodd"
                    />
                </svg>
                Closed
                <span className="badge badge-ghost badge-xs">{tasks.length}</span>
            </button>

            {expanded && (
                <div className="mt-2 space-y-1">
                    {tasks.map((task) => (
                        <div
                            key={task.path}
                            className="group flex items-center gap-3 py-1.5 px-2 rounded hover:bg-base-200 transition-colors"
                        >
                            <button
                                onClick={() => onEdit(task)}
                                className="text-sm text-base-content/60 hover:text-primary truncate flex-1 text-left transition-colors"
                            >
                                {task.name}
                            </button>
                            <span className="text-xs text-base-content/40 shrink-0">
                                {agentName(task.assignee)}
                            </span>
                            <span
                                className={`badge badge-soft badge-xs uppercase font-bold shrink-0 ${PRIORITY_BADGE[task.priority] || "badge-info"
                                    }`}
                            >
                                {task.priority}
                            </span>
                            {task.responses?.length > 0 && (
                                <span className="badge badge-ghost badge-xs shrink-0">
                                    {task.responses.length} {task.responses.length === 1 ? "reply" : "replies"}
                                </span>
                            )}
                            <button
                                onClick={() => onReopen(task.path)}
                                className="btn btn-ghost btn-xs text-[10px] opacity-0 group-hover:opacity-100 transition-opacity shrink-0"
                                title="Reopen task"
                            >
                                Reopen
                            </button>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}

const PRIORITY_ORDER: Record<string, number> = { p0: 0, p1: 1, p2: 2, p3: 3 };

function sortTasks(tasks: Task[], sort: SortKey): Task[] {
    const sorted = [...tasks];
    switch (sort) {
        case "oldest":
            return sorted.sort(
                (a, b) => (a.created_at || "").localeCompare(b.created_at || "")
            );
        case "priority":
            return sorted.sort(
                (a, b) =>
                    (PRIORITY_ORDER[a.priority] ?? 9) -
                    (PRIORITY_ORDER[b.priority] ?? 9)
            );
        case "due_date":
            return sorted.sort((a, b) => {
                if (!a.due_date) return 1;
                if (!b.due_date) return -1;
                return a.due_date.localeCompare(b.due_date);
            });
        case "newest":
        default:
            return sorted.sort(
                (a, b) => (b.created_at || "").localeCompare(a.created_at || "")
            );
    }
}

export function TaskBoardView() {
    const { data: tasks = [], isLoading: loading, isError: error, refetch: fetchTasks } =
        useTasks();
    const createTaskMutation = useCreateTask();
    const updateTaskMutation = useUpdateTask();
    const { data: agents = [] } = useAgents();
    const [showCreate, setShowCreate] = useState(false);
    const [editingTask, setEditingTask] = useState<Task | null>(null);
    const [showClosed, setShowClosed] = useState(false);
    const [filters, setFilters] = useState<TaskFilters>({
        search: "",
        assignee: "",
        priority: "",
        sort: "newest",
    });

    const { activeTasks, closedTasks, filtered } = useMemo(() => {
        const active = tasks.filter((t) => t.status !== "closed");
        const closed = tasks.filter((t) => t.status === "closed");

        let result = active;
        if (filters.search) {
            const q = filters.search.toLowerCase();
            result = result.filter(
                (t) =>
                    t.name.toLowerCase().includes(q) ||
                    t.body?.toLowerCase().includes(q) ||
                    t.labels?.some((l) => l.toLowerCase().includes(q))
            );
        }
        if (filters.assignee) {
            result = result.filter((t) => t.assignee === filters.assignee);
        }
        if (filters.priority) {
            result = result.filter((t) => t.priority === filters.priority);
        }
        return {
            activeTasks: active,
            closedTasks: sortTasks(closed, "newest"),
            filtered: sortTasks(result, filters.sort),
        };
    }, [tasks, filters]);

    const handleStatusChange = (path: string, status: string) => {
        updateTaskMutation.mutate({ path, data: { status } });
    };

    const handleDrop = (taskPath: string, newStatus: string) => {
        updateTaskMutation.mutate({ path: taskPath, data: { status: newStatus } });
    };

    const grouped = COLUMNS.map((col) => ({
        ...col,
        tasks: filtered.filter((t) => t.status === col.key),
    }));

    return (
        <div className="h-full flex flex-col">
            <div className="flex items-center justify-between px-6 py-4 border-b border-neutral">
                <div>
                    <h1 className="text-xl font-bold text-base-content">Tasks</h1>
                    {activeTasks.length > 0 && (
                        <p className="text-xs text-base-content/60 mt-0.5">
                            {activeTasks.length} active task{activeTasks.length !== 1 ? "s" : ""}
                            {closedTasks.length > 0 && ` · ${closedTasks.length} closed`}
                        </p>
                    )}
                </div>
                <button onClick={() => setShowCreate(true)} className="btn btn-primary btn-sm">
                    + New Task
                </button>
            </div>

            <TaskFilterBar
                filters={filters}
                onChange={setFilters}
                taskCount={activeTasks.length}
                filteredCount={filtered.length}
            />

            {loading ? (
                <div className="flex-1 flex items-center justify-center">
                    <span className="loading loading-spinner loading-md text-primary" />
                </div>
            ) : error ? (
                <div className="flex-1 flex items-center justify-center">
                    <div className="text-center">
                        <p className="text-sm text-error mb-2">Tasks aren't loading right now. Try refreshing the page.</p>
                        <button onClick={() => fetchTasks()} className="link link-accent text-xs">
                            Try again
                        </button>
                    </div>
                </div>
            ) : (
                <div className="flex-1 overflow-y-auto">
                    <div className="overflow-x-auto p-4">
                        <div className="flex gap-4 min-h-[300px] min-w-max">
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

                    {closedTasks.length > 0 && (
                        <ClosedTasksList
                            tasks={closedTasks}
                            agents={agents}
                            expanded={showClosed}
                            onToggle={() => setShowClosed(!showClosed)}
                            onReopen={(path) => updateTaskMutation.mutate({ path, data: { status: "pending" } })}
                            onEdit={setEditingTask}
                        />
                    )}
                </div>
            )}

            {showCreate && (
                <CreateTaskModal
                    onClose={() => setShowCreate(false)}
                    onCreate={(data) => createTaskMutation.mutate(data)}
                />
            )}

            {editingTask && (
                <TaskEditModal
                    task={editingTask}
                    onClose={() => setEditingTask(null)}
                    onSave={(path, data) => updateTaskMutation.mutate({ path, data })}
                />
            )}
        </div>
    );
}
