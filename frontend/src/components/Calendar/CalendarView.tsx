import { useEffect, useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { useCalendarStore, type CalendarEvent } from "../../stores/calendarStore";
import { useTaskStore } from "../../stores/taskStore";
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
    events,
    loading,
    viewMode,
    currentDate,
    filters,
    fetchEvents,
  } = useCalendarStore();
  const { createTask } = useTaskStore();

  const navigate = useNavigate();
  const [selectedEvent, setSelectedEvent] = useState<CalendarEvent | null>(null);
  const [createDate, setCreateDate] = useState<string | null>(null);

  // Compute date range based on view mode
  const fetchRange = useCallback(() => {
    let start: string;
    let end: string;

    if (viewMode === "month") {
      const first = firstOfMonth(currentDate);
      const last = lastOfMonth(currentDate);
      const gridStart = new Date(first);
      gridStart.setDate(gridStart.getDate() - gridStart.getDay());
      const gridEnd = new Date(last);
      gridEnd.setDate(gridEnd.getDate() + (6 - gridEnd.getDay()));
      start = formatDate(gridStart);
      end = formatDate(gridEnd);
    } else {
      const dates = weekGridDates(currentDate);
      start = formatDate(dates[0]);
      end = formatDate(dates[6]);
    }

    fetchEvents(start, end);
  }, [viewMode, currentDate, filters, fetchEvents]);

  useEffect(() => {
    fetchRange();
  }, [fetchRange]);

  const handleEditTask = () => {
    setSelectedEvent(null);
    navigate("/tasks");
  };

  const handleDateClick = (dateStr: string) => {
    setCreateDate(dateStr);
  };

  const handleCreateTask = async (data: Parameters<typeof createTask>[0]) => {
    await createTask(data);
    setCreateDate(null);
    fetchRange();
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
