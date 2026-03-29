import { useEffect, useRef } from "react";
import type { CalendarEvent } from "../../stores/calendarStore";
import { eventColor, SOURCE_COLORS } from "./calendarUtils";

const SOURCE_LABELS: Record<string, string> = {
  task: "Task",
  scheduled_action: "Scheduled Action",
  sandbox: "Sandbox",
};

const STATUS_BADGES: Record<string, string> = {
  pending: "badge-warning",
  in_progress: "badge-info",
  done: "badge-success",
  blocked: "badge-error",
  running: "badge-info",
};

export function EventDetailModal({
  event,
  onClose,
  onEditTask,
}: {
  event: CalendarEvent;
  onClose: () => void;
  onEditTask?: (taskPath: string) => void;
}) {
  const dialogRef = useRef<HTMLDialogElement>(null);
  const color = eventColor(event);

  useEffect(() => {
    dialogRef.current?.showModal();
  }, []);

  return (
    <dialog ref={dialogRef} className="modal" onClose={onClose}>
      <div className="modal-box max-w-md">
        <div className="flex items-center gap-2 mb-4">
          <div
            className="w-3 h-3 rounded-full flex-shrink-0"
            style={{ backgroundColor: color }}
          />
          <h3 className="text-lg font-bold truncate">{event.title}</h3>
        </div>

        <div className="space-y-3 text-sm">
          <div className="flex items-center gap-2">
            <span className="text-base-content/60 w-20">Source</span>
            <span className="badge badge-sm badge-ghost">
              {SOURCE_LABELS[event.source] || event.source}
            </span>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-base-content/60 w-20">Date</span>
            <span>
              {event.start_date}
              {event.end_date && event.end_date !== event.start_date && (
                <> &rarr; {event.end_date}</>
              )}
            </span>
          </div>

          {event.agent_name && (
            <div className="flex items-center gap-2">
              <span className="text-base-content/60 w-20">Agent</span>
              <div className="flex items-center gap-1.5">
                <div
                  className="w-2 h-2 rounded-full"
                  style={{ backgroundColor: event.agent_color || "#6B7280" }}
                />
                <span>{event.agent_name}</span>
              </div>
            </div>
          )}

          {event.status && (
            <div className="flex items-center gap-2">
              <span className="text-base-content/60 w-20">Status</span>
              <span
                className={`badge badge-sm ${STATUS_BADGES[event.status] || "badge-ghost"}`}
              >
                {event.status.replace("_", " ")}
              </span>
            </div>
          )}

          {event.priority && (
            <div className="flex items-center gap-2">
              <span className="text-base-content/60 w-20">Priority</span>
              <span className="badge badge-sm badge-ghost uppercase">
                {event.priority}
              </span>
            </div>
          )}

          {/* Source-specific metadata */}
          {event.source === "task" &&
            Array.isArray(event.metadata.labels) &&
            event.metadata.labels.length > 0 && (
              <div className="flex items-center gap-2">
                <span className="text-base-content/60 w-20">Labels</span>
                <div className="flex flex-wrap gap-1">
                  {(event.metadata.labels as string[]).map((l: string) => (
                    <span key={l} className="badge badge-xs badge-ghost">
                      {l}
                    </span>
                  ))}
                </div>
              </div>
            )}

          {event.source === "task" && event.metadata.estimated_hours != null && (
            <div className="flex items-center gap-2">
              <span className="text-base-content/60 w-20">Estimate</span>
              <span>{String(event.metadata.estimated_hours)}h</span>
            </div>
          )}

          {event.source === "scheduled_action" && Boolean(event.metadata.description) && (
            <div className="flex items-center gap-2">
              <span className="text-base-content/60 w-20">Info</span>
              <span className="text-base-content/80">
                {String(event.metadata.description)}
              </span>
            </div>
          )}

          {event.source === "sandbox" && Boolean(event.metadata.sandbox_id) && (
            <div className="flex items-center gap-2">
              <span className="text-base-content/60 w-20">Container</span>
              <code className="text-xs bg-base-200 px-1.5 py-0.5 rounded">
                {String(event.metadata.sandbox_id)}
              </code>
            </div>
          )}
        </div>

        <div className="modal-action">
          {event.source === "task" && onEditTask && Boolean(event.metadata.path) && (
            <button
              onClick={() => onEditTask(event.metadata.path as string)}
              className="btn btn-primary btn-sm"
            >
              Edit Task
            </button>
          )}
          <button onClick={onClose} className="btn btn-ghost btn-sm">
            Close
          </button>
        </div>
      </div>
      <form method="dialog" className="modal-backdrop">
        <button>close</button>
      </form>
    </dialog>
  );
}
