import { useCalendarStore, type CalendarSource } from "../../stores/calendarStore";
import { useAgentStore } from "../../stores/agentStore";
import { monthLabel, weekLabel, weekGridDates } from "./calendarUtils";

const SOURCE_OPTIONS: { value: string; label: string }[] = [
  { value: "", label: "All Sources" },
  { value: "task", label: "Tasks" },
  { value: "scheduled_action", label: "Scheduled Actions" },
  { value: "sandbox", label: "Sandboxes" },
];

export function CalendarToolbar() {
  const {
    viewMode,
    currentDate,
    filters,
    setViewMode,
    setFilters,
    navigateForward,
    navigateBackward,
    navigateToday,
  } = useCalendarStore();
  const agents = useAgentStore((s) => s.agents);

  const periodLabel =
    viewMode === "month"
      ? monthLabel(currentDate)
      : weekLabel(weekGridDates(currentDate));

  return (
    <div className="flex flex-wrap items-center gap-3 px-4 py-3">
      {/* Navigation */}
      <div className="flex items-center gap-1">
        <button
          onClick={navigateBackward}
          className="btn btn-ghost btn-sm btn-square"
          aria-label="Previous"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} className="w-4 h-4">
            <path d="M15 19l-7-7 7-7" />
          </svg>
        </button>
        <button
          onClick={navigateToday}
          className="btn btn-ghost btn-sm"
        >
          Today
        </button>
        <button
          onClick={navigateForward}
          className="btn btn-ghost btn-sm btn-square"
          aria-label="Next"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} className="w-4 h-4">
            <path d="M9 5l7 7-7 7" />
          </svg>
        </button>
      </div>

      {/* Period label */}
      <h2 className="font-[family-name:var(--font-display)] text-lg font-bold tracking-tight min-w-[180px]">
        {periodLabel}
      </h2>

      <div className="flex-1" />

      {/* Filters */}
      <select
        value={filters.agentId || ""}
        onChange={(e) => setFilters({ agentId: e.target.value || null })}
        className="select select-sm"
        aria-label="Filter by agent"
      >
        <option value="">All Agents</option>
        {agents
          .filter((a) => a.id !== "axon")
          .map((a) => (
            <option key={a.id} value={a.id}>
              {a.name}
            </option>
          ))}
      </select>

      <select
        value={filters.source || ""}
        onChange={(e) =>
          setFilters({ source: (e.target.value || null) as CalendarSource | null })
        }
        className="select select-sm"
        aria-label="Filter by source"
      >
        {SOURCE_OPTIONS.map((o) => (
          <option key={o.value} value={o.value}>
            {o.label}
          </option>
        ))}
      </select>

      {/* View toggle */}
      <div className="join">
        <button
          onClick={() => setViewMode("month")}
          className={`btn btn-sm join-item ${viewMode === "month" ? "btn-active" : ""}`}
        >
          Month
        </button>
        <button
          onClick={() => setViewMode("week")}
          className={`btn btn-sm join-item ${viewMode === "week" ? "btn-active" : ""}`}
        >
          Week
        </button>
      </div>
    </div>
  );
}
