import { create } from "zustand";
import { orgApiPath } from "./orgStore";

export interface UsageRecord {
  ts: string;
  model: string;
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
  cost: number;
  agent_id: string;
  call_type: string;
  caller: string;
}

export interface BreakdownEntry {
  cost: number;
  tokens: number;
  count: number;
}

export interface UsageSummary {
  total_cost: number;
  total_tokens: number;
  total_requests: number;
  by_model: Record<string, BreakdownEntry>;
  by_agent: Record<string, BreakdownEntry>;
}

export type Period = "today" | "7d" | "30d" | "all";

interface UsageState {
  summary: UsageSummary | null;
  records: UsageRecord[];
  total: number;
  loading: boolean;
  error: boolean;
  period: Period;
  setPeriod: (p: Period) => void;
  fetchSummary: () => Promise<void>;
  fetchRecords: (limit?: number, offset?: number) => Promise<void>;
}

function dateRange(period: Period): { date_from?: string; date_to?: string } {
  if (period === "all") return {};
  const now = new Date();
  const to = now.toISOString().slice(0, 10);
  if (period === "today") return { date_from: to, date_to: to };
  const days = period === "7d" ? 7 : 30;
  const from = new Date(now.getTime() - days * 86400000).toISOString().slice(0, 10);
  return { date_from: from, date_to: to };
}

function buildQs(params: Record<string, string | number | undefined>): string {
  const qs = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined) qs.set(k, String(v));
  }
  const s = qs.toString();
  return s ? `?${s}` : "";
}

export const useUsageStore = create<UsageState>((set, get) => ({
  summary: null,
  records: [],
  total: 0,
  loading: false,
  error: false,
  period: "30d",

  setPeriod: (p) => {
    set({ period: p });
    get().fetchSummary();
    get().fetchRecords();
  },

  fetchSummary: async () => {
    set({ loading: true, error: false });
    try {
      const range = dateRange(get().period);
      const res = await fetch(orgApiPath("usage/summary") + buildQs(range));
      const data = await res.json();
      set({ summary: data, loading: false });
    } catch {
      set({ error: true, loading: false });
    }
  },

  fetchRecords: async (limit = 100, offset = 0) => {
    try {
      const range = dateRange(get().period);
      const res = await fetch(
        orgApiPath("usage") + buildQs({ ...range, limit, offset }),
      );
      const data = await res.json();
      set({ records: data.records || [], total: data.total || 0 });
    } catch {
      set({ error: true });
    }
  },
}));
