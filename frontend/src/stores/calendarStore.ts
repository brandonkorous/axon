import { create } from "zustand";
import { orgApiPath } from "./orgStore";

export type CalendarSource = "task" | "scheduled_action" | "sandbox";
export type CalendarViewMode = "month" | "week";

export interface CalendarEvent {
  id: string;
  title: string;
  start_date: string; // YYYY-MM-DD
  end_date: string | null;
  start_time: string | null;
  end_time: string | null;
  source: CalendarSource;
  agent_id: string | null;
  agent_name: string | null;
  agent_color: string | null;
  status: string | null;
  priority: string | null;
  metadata: Record<string, unknown>;
}

interface CalendarFilters {
  agentId: string | null;
  source: CalendarSource | null;
}

interface CalendarStore {
  events: CalendarEvent[];
  loading: boolean;
  error: string | null;
  viewMode: CalendarViewMode;
  currentDate: Date;
  filters: CalendarFilters;
  fetchEvents: (start: string, end: string) => Promise<void>;
  setViewMode: (mode: CalendarViewMode) => void;
  setCurrentDate: (date: Date) => void;
  setFilters: (filters: Partial<CalendarFilters>) => void;
  navigateForward: () => void;
  navigateBackward: () => void;
  navigateToday: () => void;
}

export const useCalendarStore = create<CalendarStore>((set, get) => ({
  events: [],
  loading: false,
  error: null,
  viewMode: "month",
  currentDate: new Date(),
  filters: { agentId: null, source: null },

  fetchEvents: async (start, end) => {
    set({ loading: true, error: null });
    try {
      const params = new URLSearchParams({ start, end });
      const { filters } = get();
      if (filters.agentId) params.set("agent_id", filters.agentId);
      if (filters.source) params.set("source", filters.source);
      const url = orgApiPath("calendar") + `?${params}`;
      const res = await fetch(url);
      if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
      const events = await res.json();
      set({ events, loading: false });
    } catch (e) {
      set({ loading: false, error: (e as Error).message });
    }
  },

  setViewMode: (viewMode) => set({ viewMode }),
  setCurrentDate: (currentDate) => set({ currentDate }),

  setFilters: (partial) =>
    set((s) => ({ filters: { ...s.filters, ...partial } })),

  navigateForward: () => {
    const { currentDate, viewMode } = get();
    const next = new Date(currentDate);
    if (viewMode === "month") {
      next.setMonth(next.getMonth() + 1);
    } else {
      next.setDate(next.getDate() + 7);
    }
    set({ currentDate: next });
  },

  navigateBackward: () => {
    const { currentDate, viewMode } = get();
    const prev = new Date(currentDate);
    if (viewMode === "month") {
      prev.setMonth(prev.getMonth() - 1);
    } else {
      prev.setDate(prev.getDate() - 7);
    }
    set({ currentDate: prev });
  },

  navigateToday: () => set({ currentDate: new Date() }),
}));
