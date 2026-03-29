import type { CalendarEvent } from "../../stores/calendarStore";
import { eventColor } from "./calendarUtils";

const SOURCE_ICONS: Record<string, string> = {
  task: "\u2022", // bullet
  scheduled_action: "\u21BB", // cycle arrow
  sandbox: "\u25A3", // filled square
};

export function EventChip({
  event,
  onClick,
}: {
  event: CalendarEvent;
  onClick: (event: CalendarEvent) => void;
}) {
  const color = eventColor(event);
  const icon = SOURCE_ICONS[event.source] || "\u2022";

  return (
    <button
      onClick={(e) => {
        e.stopPropagation();
        onClick(event);
      }}
      className="flex items-center gap-1 w-full text-left text-xs px-1.5 py-0.5 rounded truncate hover:opacity-80 transition-opacity cursor-pointer"
      style={{ backgroundColor: `${color}20`, color }}
      title={event.title}
    >
      <span className="flex-shrink-0 text-[10px]">{icon}</span>
      <span className="truncate">{event.title}</span>
      {event.priority && event.source === "task" && (
        <span className="flex-shrink-0 opacity-60 text-[10px] uppercase">
          {event.priority}
        </span>
      )}
    </button>
  );
}
