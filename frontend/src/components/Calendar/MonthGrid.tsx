import { useMemo } from "react";
import type { CalendarEvent } from "../../stores/calendarStore";
import { EventChip } from "./EventChip";
import {
  monthGridDates,
  formatDate,
  eventOnDate,
  isSameDay,
  weekdayLabel,
} from "./calendarUtils";

const MAX_VISIBLE_EVENTS = 3;

export function MonthGrid({
  currentDate,
  events,
  onEventClick,
}: {
  currentDate: Date;
  events: CalendarEvent[];
  onEventClick: (event: CalendarEvent) => void;
}) {
  const dates = useMemo(() => monthGridDates(currentDate), [currentDate]);
  const today = new Date();
  const currentMonth = currentDate.getMonth();

  return (
    <div className="flex flex-col flex-1 overflow-hidden">
      {/* Weekday header */}
      <div className="grid grid-cols-7 border-b border-base-300">
        {Array.from({ length: 7 }, (_, i) => (
          <div
            key={i}
            className="px-2 py-1.5 text-xs font-medium text-base-content/60 text-center"
          >
            {weekdayLabel(i)}
          </div>
        ))}
      </div>

      {/* Day cells */}
      <div className="grid grid-cols-7 flex-1 auto-rows-fr overflow-hidden">
        {dates.map((date) => {
          const dateStr = formatDate(date);
          const isToday = isSameDay(date, today);
          const isCurrentMonth = date.getMonth() === currentMonth;
          const dayEvents = events.filter((e) => eventOnDate(e, dateStr));
          const overflow = dayEvents.length - MAX_VISIBLE_EVENTS;

          return (
            <div
              key={dateStr}
              className={`border-b border-r border-base-300 p-1 min-h-0 overflow-hidden flex flex-col ${
                isCurrentMonth ? "" : "opacity-40"
              }`}
            >
              <div className="flex items-center justify-center mb-0.5">
                <span
                  className={`text-xs w-6 h-6 flex items-center justify-center rounded-full ${
                    isToday
                      ? "bg-primary text-primary-content font-bold"
                      : "text-base-content/80"
                  }`}
                >
                  {date.getDate()}
                </span>
              </div>
              <div className="flex flex-col gap-0.5 min-h-0 overflow-hidden">
                {dayEvents.slice(0, MAX_VISIBLE_EVENTS).map((event) => (
                  <EventChip
                    key={event.id}
                    event={event}
                    onClick={onEventClick}
                  />
                ))}
                {overflow > 0 && (
                  <span className="text-[10px] text-base-content/50 text-center">
                    +{overflow} more
                  </span>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
