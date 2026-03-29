import { useMemo } from "react";
import type { CalendarEvent } from "../../stores/calendarStore";
import { EventChip } from "./EventChip";
import {
  weekGridDates,
  formatDate,
  eventOnDate,
  isSameDay,
  weekdayLabel,
} from "./calendarUtils";

export function WeekGrid({
  currentDate,
  events,
  onEventClick,
  onDateClick,
}: {
  currentDate: Date;
  events: CalendarEvent[];
  onEventClick: (event: CalendarEvent) => void;
  onDateClick?: (dateStr: string) => void;
}) {
  const dates = useMemo(() => weekGridDates(currentDate), [currentDate]);
  const today = new Date();

  return (
    <div className="flex flex-col flex-1 overflow-hidden">
      {/* Day columns */}
      <div className="grid grid-cols-7 flex-1 overflow-hidden">
        {dates.map((date, i) => {
          const dateStr = formatDate(date);
          const isToday = isSameDay(date, today);
          const dayEvents = events.filter((e) => eventOnDate(e, dateStr));

          return (
            <div
              key={dateStr}
              onClick={() => onDateClick?.(dateStr)}
              className="border-r border-base-300 flex flex-col overflow-hidden cursor-pointer hover:bg-base-200/50 transition-colors"
            >
              {/* Day header */}
              <div
                className={`px-2 py-2 text-center border-b border-base-300 ${
                  isToday ? "bg-primary/5" : ""
                }`}
              >
                <div className="text-xs text-base-content/60">
                  {weekdayLabel(i)}
                </div>
                <div
                  className={`text-lg font-bold mt-0.5 ${
                    isToday ? "text-primary" : "text-base-content"
                  }`}
                >
                  {date.getDate()}
                </div>
              </div>

              {/* Events */}
              <div className="flex-1 overflow-y-auto p-1 space-y-1">
                {dayEvents.length === 0 && (
                  <div className="text-xs text-base-content/30 text-center mt-4">
                    No events
                  </div>
                )}
                {dayEvents.map((event) => (
                  <EventChip
                    key={event.id}
                    event={event}
                    onClick={onEventClick}
                  />
                ))}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
