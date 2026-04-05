import { useAgents } from "../../hooks/useAgents";

const PRIORITIES = [
  { key: "", label: "All priorities" },
  { key: "p0", label: "P0" },
  { key: "p1", label: "P1" },
  { key: "p2", label: "P2" },
  { key: "p3", label: "P3" },
] as const;

const SORT_OPTIONS = [
  { key: "newest", label: "Newest first" },
  { key: "oldest", label: "Oldest first" },
  { key: "priority", label: "Priority" },
  { key: "due_date", label: "Due date" },
] as const;

export type SortKey = (typeof SORT_OPTIONS)[number]["key"];

export interface TaskFilters {
  search: string;
  assignee: string;
  priority: string;
  sort: SortKey;
}

export function TaskFilterBar({
  filters,
  onChange,
  taskCount,
  filteredCount,
}: {
  filters: TaskFilters;
  onChange: (filters: TaskFilters) => void;
  taskCount: number;
  filteredCount: number;
}) {
  const { data: agents = [] } = useAgents();
  const isFiltered = filters.search || filters.assignee || filters.priority;

  return (
    <div className="flex items-center gap-2 px-6 py-2 border-b border-neutral bg-base-200/50">
      {/* Search */}
      <div className="relative flex-1 max-w-xs">
        <svg
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 16 16"
          fill="currentColor"
          className="size-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-base-content/40"
        >
          <path
            fillRule="evenodd"
            d="M9.965 11.026a5 5 0 1 1 1.06-1.06l2.755 2.754a.75.75 0 1 1-1.06 1.06l-2.755-2.754ZM10.5 7a3.5 3.5 0 1 1-7 0 3.5 3.5 0 0 1 7 0Z"
            clipRule="evenodd"
          />
        </svg>
        <input
          type="text"
          value={filters.search}
          onChange={(e) => onChange({ ...filters, search: e.target.value })}
          placeholder="Search tasks..."
          className="input input-sm w-full pl-8"
          aria-label="Search tasks"
        />
      </div>

      {/* Assignee */}
      <select
        value={filters.assignee}
        onChange={(e) => onChange({ ...filters, assignee: e.target.value })}
        className="select select-sm"
        aria-label="Filter by assignee"
      >
        <option value="">All agents</option>
        {agents
          .filter((a) => a.id !== "axon")
          .map((a) => (
            <option key={a.id} value={a.id}>
              {a.name}
            </option>
          ))}
      </select>

      {/* Priority */}
      <select
        value={filters.priority}
        onChange={(e) => onChange({ ...filters, priority: e.target.value })}
        className="select select-sm"
        aria-label="Filter by priority"
      >
        {PRIORITIES.map((p) => (
          <option key={p.key} value={p.key}>
            {p.label}
          </option>
        ))}
      </select>

      {/* Sort */}
      <select
        value={filters.sort}
        onChange={(e) =>
          onChange({ ...filters, sort: e.target.value as SortKey })
        }
        className="select select-sm"
        aria-label="Sort tasks"
      >
        {SORT_OPTIONS.map((s) => (
          <option key={s.key} value={s.key}>
            {s.label}
          </option>
        ))}
      </select>

      {/* Filter status */}
      {isFiltered && (
        <div className="flex items-center gap-2 ml-1">
          <span className="text-xs text-base-content/50">
            {filteredCount}/{taskCount}
          </span>
          <button
            onClick={() =>
              onChange({ search: "", assignee: "", priority: "", sort: "newest" })
            }
            className="btn btn-ghost btn-xs text-base-content/50"
            aria-label="Clear filters"
          >
            Clear
          </button>
        </div>
      )}
    </div>
  );
}
