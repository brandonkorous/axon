import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useCalendarStore, type CalendarEvent } from "../../stores/calendarStore";
import { useCalendarEvents } from "../../hooks/useCalendar";
import { useCreateTask, type CreateTaskInput } from "../../hooks/useTasks";
import { CalendarToolbar } from "./CalendarToolbar";
import { MonthGrid } from "./MonthGrid";
import { WeekGrid } from "./WeekGrid";
import { EventDetailModal } from "./EventDetailModal";
import { CreateTaskModal } from "../Tasks/CreateTaskModal";
import {
  formatDate,
  firstOfMonth,
  lastOfMonth,
  weekGridDates,
} from "./calendarUtils";

export function CalendarView() {
  const {
    viewMode,
    currentDate,
    filters,
  } = useCalendarStore();
  const createTaskMutation = useCreateTask();

  const navigate = useNavigate();
  const [selectedEvent, setSelectedEvent] = useState<CalendarEvent | null>(null);
  const [createDate, setCreateDate] = useState<string | null>(null);

  // Compute date range based on view mode
  const { start, end } = useMemo(() => {
    if (viewMode === "month") {
      const first = firstOfMonth(currentDate);
      const last = lastOfMonth(currentDate);
      const gridStart = new Date(first);
      gridStart.setDate(gridStart.getDate() - gridStart.getDay());
      const gridEnd = new Date(last);
      gridEnd.setDate(gridEnd.getDate() + (6 - gridEnd.getDay()));
      return { start: formatDate(gridStart), end: formatDate(gridEnd) };
    }
    const dates = weekGridDates(currentDate);
    return { start: formatDate(dates[0]), end: formatDate(dates[6]) };
  }, [viewMode, currentDate]);

  const { data: eventsData, isLoading: loading } = useCalendarEvents(
    start,
    end,
    filters.agentId ?? undefined,
    filters.source ?? undefined,
  );
  const events = (eventsData ?? []) as CalendarEvent[];

  const handleEditTask = () => {
    setSelectedEvent(null);
    navigate("/tasks");
  };

  const handleDateClick = (dateStr: string) => {
    setCreateDate(dateStr);
  };

  const handleCreateTask = async (data: CreateTaskInput) => {
    await createTaskMutation.mutateAsync(data);
    setCreateDate(null);
  };

  return (
    <div className="h-full flex flex-col overflow-hidden">
      <CalendarToolbar onNewTask={() => setCreateDate(formatDate(new Date()))} />

      {loading && events.length === 0 ? (
        <div className="flex-1 flex items-center justify-center">
          <span className="loading loading-spinner loading-md text-primary" />
        </div>
      ) : (
        <div className="flex-1 overflow-hidden flex flex-col">
          {viewMode === "month" ? (
            <MonthGrid
              currentDate={currentDate}
              events={events}
              onEventClick={setSelectedEvent}
              onDateClick={handleDateClick}
            />
          ) : (
            <WeekGrid
              currentDate={currentDate}
              events={events}
              onEventClick={setSelectedEvent}
              onDateClick={handleDateClick}
            />
          )}
        </div>
      )}

      {selectedEvent && (
        <EventDetailModal
          event={selectedEvent}
          onClose={() => setSelectedEvent(null)}
          onEditTask={handleEditTask}
        />
      )}

      {createDate && (
        <CreateTaskModal
          onClose={() => setCreateDate(null)}
          onCreate={handleCreateTask}
          defaultDate={createDate}
        />
      )}
    </div>
  );
}
