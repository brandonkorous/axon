import type { CalendarEvent } from "../../stores/calendarStore";

/** Source-type fallback colors (when no agent color available). */
export const SOURCE_COLORS: Record<string, string> = {
  task: "#609894", // primary teal
  scheduled_action: "#7A8B5C", // accent olive
  sandbox: "#C4785B", // secondary terracotta
};

/** Get display color for an event. */
export function eventColor(event: CalendarEvent): string {
  return event.agent_color || SOURCE_COLORS[event.source] || "#6B7280";
}

/** Format a date as YYYY-MM-DD. */
export function formatDate(date: Date): string {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, "0");
  const d = String(date.getDate()).padStart(2, "0");
  return `${y}-${m}-${d}`;
}

/** Get the first day of the month. */
export function firstOfMonth(date: Date): Date {
  return new Date(date.getFullYear(), date.getMonth(), 1);
}

/** Get the last day of the month. */
export function lastOfMonth(date: Date): Date {
  return new Date(date.getFullYear(), date.getMonth() + 1, 0);
}

/** Get the Monday-start week containing the given date. */
export function weekStart(date: Date): Date {
  const d = new Date(date);
  const day = d.getDay();
  const diff = day === 0 ? -6 : 1 - day; // Monday start
  d.setDate(d.getDate() + diff);
  return d;
}

/** Build an array of dates for the calendar month grid (always starts Sunday). */
export function monthGridDates(date: Date): Date[] {
  const first = firstOfMonth(date);
  const last = lastOfMonth(date);

  // Start from the Sunday before (or on) the first of the month
  const start = new Date(first);
  start.setDate(start.getDate() - start.getDay());

  // End on the Saturday after (or on) the last of the month
  const end = new Date(last);
  const remaining = 6 - end.getDay();
  end.setDate(end.getDate() + remaining);

  const dates: Date[] = [];
  const current = new Date(start);
  while (current <= end) {
    dates.push(new Date(current));
    current.setDate(current.getDate() + 1);
  }
  return dates;
}

/** Build an array of 7 dates for a week (Sunday start). */
export function weekGridDates(date: Date): Date[] {
  const start = new Date(date);
  start.setDate(start.getDate() - start.getDay());
  const dates: Date[] = [];
  for (let i = 0; i < 7; i++) {
    const d = new Date(start);
    d.setDate(d.getDate() + i);
    dates.push(d);
  }
  return dates;
}

/** Check if an event falls on a specific date. */
export function eventOnDate(event: CalendarEvent, dateStr: string): boolean {
  if (event.end_date) {
    return event.start_date <= dateStr && event.end_date >= dateStr;
  }
  return event.start_date === dateStr;
}

/** Check if two dates are the same calendar day. */
export function isSameDay(a: Date, b: Date): boolean {
  return (
    a.getFullYear() === b.getFullYear() &&
    a.getMonth() === b.getMonth() &&
    a.getDate() === b.getDate()
  );
}

const WEEKDAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

export function weekdayLabel(index: number): string {
  return WEEKDAYS[index] || "";
}

const MONTHS = [
  "January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December",
];

export function monthLabel(date: Date): string {
  return `${MONTHS[date.getMonth()]} ${date.getFullYear()}`;
}

export function weekLabel(dates: Date[]): string {
  if (dates.length === 0) return "";
  const first = dates[0];
  const last = dates[dates.length - 1];
  const opts: Intl.DateTimeFormatOptions = { month: "short", day: "numeric" };
  const f = first.toLocaleDateString("en-US", opts);
  const l = last.toLocaleDateString("en-US", { ...opts, year: "numeric" });
  return `${f} - ${l}`;
}
