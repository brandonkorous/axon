import { create } from "zustand";
import { orgApiPath } from "./orgStore";

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
}

interface ApprovalStore {
  approvals: Approval[];
  loading: boolean;
  fetchPending: () => Promise<void>;
  approve: (taskPath: string) => Promise<boolean>;
  decline: (taskPath: string, reason?: string) => Promise<boolean>;
}

export const useApprovalStore = create<ApprovalStore>((set, get) => ({
  approvals: [],
  loading: false,

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
