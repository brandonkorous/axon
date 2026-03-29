import { create } from "zustand";
import { orgApiPath } from "./orgStore";

export interface CommsPayload {
  to?: string;
  subject?: string;
  body?: string;
  cc?: string;
  target?: string;
  content?: string;
  is_dm?: boolean;
}

export interface Approval {
  task_path: string;
  title: string;
  plan_content: string;
  files_affected: string[];
  delegated_by: string;
  assignee: string;
  priority: string;
  created_at: string;
  updated_at: string;
  // Comms-specific fields (present when type === "comms_outbound")
  type?: string;
  channel?: string;
  comms_payload?: string; // JSON string of CommsPayload
}

export interface ApprovalHistoryItem {
  task_path: string;
  title: string;
  status: "approved" | "declined" | "send_failed";
  created_by: string;
  created_at: string;
  updated_at: string;
  type?: string;
  channel?: string;
  comms_payload?: string;
  send_result?: string;
  approved_at?: string;
  decline_reason?: string;
}

interface ApprovalStore {
  approvals: Approval[];
  loading: boolean;
  history: ApprovalHistoryItem[];
  historyLoading: boolean;
  fetchPending: () => Promise<void>;
  fetchHistory: (filters?: { status?: string; channel?: string }) => Promise<void>;
  approve: (taskPath: string) => Promise<boolean>;
  decline: (taskPath: string, reason?: string) => Promise<boolean>;
}

export const useApprovalStore = create<ApprovalStore>((set, get) => ({
  approvals: [],
  loading: false,
  history: [],
  historyLoading: false,

  fetchPending: async () => {
    set({ loading: true });
    try {
      const res = await fetch(orgApiPath("approvals/pending"));
      const data = await res.json();
      set({ approvals: Array.isArray(data) ? data : [], loading: false });
    } catch {
      set({ loading: false });
    }
  },

  fetchHistory: async (filters) => {
    set({ historyLoading: true });
    try {
      const params = new URLSearchParams();
      if (filters?.status) params.set("status", filters.status);
      if (filters?.channel) params.set("channel", filters.channel);
      const qs = params.toString();
      const res = await fetch(orgApiPath(`approvals/history${qs ? `?${qs}` : ""}`));
      const data = await res.json();
      set({ history: Array.isArray(data) ? data : [], historyLoading: false });
    } catch {
      set({ historyLoading: false });
    }
  },

  approve: async (taskPath: string) => {
    try {
      const res = await fetch(orgApiPath(`approvals/${taskPath}/approve`), {
        method: "POST",
      });
      if (res.ok) {
        await get().fetchPending();
        return true;
      }
      return false;
    } catch {
      return false;
    }
  },

  decline: async (taskPath: string, reason?: string) => {
    try {
      const res = await fetch(orgApiPath(`approvals/${taskPath}/decline`), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ reason: reason || "" }),
      });
      if (res.ok) {
        await get().fetchPending();
        return true;
      }
      return false;
    } catch {
      return false;
    }
  },
}));
