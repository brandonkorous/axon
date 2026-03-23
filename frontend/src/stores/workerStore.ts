import { create } from "zustand";
import { orgApiPath } from "./orgStore";

export type ProcessState = "stopped" | "running" | "paused" | "starting" | "stopping";
export type WorkerType = "code" | "documents" | "email" | "images" | "browser" | "shell";

export interface WorkerInfo {
  agent_id: string;
  name: string;
  connected: boolean;
  last_seen: string | null;
  codebase_path: string;
  worker_type: WorkerType;
  accepts_from: string[];
  color: string;
  process_state: ProcessState;
}

interface WorkerCreateData {
  name: string;
  codebase_path: string;
  worker_type: WorkerType;
  accepts_from: string[];
  color?: string;
  type_config?: Record<string, unknown>;
}

interface WorkerUpdateData {
  name?: string;
  codebase_path?: string;
  accepts_from?: string[];
  color?: string;
}

interface WorkerStore {
  workers: WorkerInfo[];
  loading: boolean;
  creating: boolean;
  createdAgentId: string | null;

  fetchWorkers: () => Promise<void>;
  fetchWorker: (agentId: string) => Promise<WorkerInfo | null>;
  createWorker: (data: WorkerCreateData) => Promise<boolean>;
  updateWorker: (agentId: string, data: WorkerUpdateData) => Promise<boolean>;
  deleteWorker: (agentId: string) => Promise<boolean>;
  startWorker: (agentId: string) => Promise<boolean>;
  stopWorker: (agentId: string) => Promise<boolean>;
  pauseWorker: (agentId: string) => Promise<boolean>;
  resumeWorker: (agentId: string) => Promise<boolean>;
  fetchLogs: (agentId: string) => Promise<string[]>;
  reset: () => void;
}

/** Optimistically set a worker's process_state in the store. */
function _optimistic(set: Function, get: Function, agentId: string, state: ProcessState) {
  const workers = get().workers.map((w: WorkerInfo) =>
    w.agent_id === agentId ? { ...w, process_state: state } : w,
  );
  set({ workers });
}

export const useWorkerStore = create<WorkerStore>((set, get) => ({
  workers: [],
  loading: false,
  creating: false,
  createdAgentId: null,

  fetchWorkers: async () => {
    const hadWorkers = get().workers.length > 0;
    if (!hadWorkers) set({ loading: true });
    try {
      const res = await fetch(orgApiPath("workers"));
      const data = await res.json();
      const incoming: WorkerInfo[] = data.workers || [];

      // Preserve transitional states (starting/stopping) until backend confirms
      const current = get().workers;
      const merged = incoming.map((w) => {
        const existing = current.find((c) => c.agent_id === w.agent_id);
        if (!existing) return w;
        const isTransitional = existing.process_state === "starting" || existing.process_state === "stopping";
        const backendConfirmed = w.process_state === "running" || w.process_state === "stopped";
        if (isTransitional && !backendConfirmed) return { ...w, process_state: existing.process_state };
        return w;
      });

      set({ workers: merged, loading: false });
    } catch {
      set({ loading: false });
    }
  },

  fetchWorker: async (agentId) => {
    try {
      const res = await fetch(orgApiPath(`workers/${agentId}`));
      if (!res.ok) return null;
      return await res.json();
    } catch {
      return null;
    }
  },

  createWorker: async (data) => {
    set({ creating: true });
    try {
      const res = await fetch(orgApiPath("workers"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });
      if (!res.ok) throw new Error("Failed to create worker");
      const result = await res.json();
      set({ creating: false, createdAgentId: result.agent_id });
      return true;
    } catch {
      set({ creating: false });
      return false;
    }
  },

  updateWorker: async (agentId, data) => {
    try {
      const res = await fetch(orgApiPath(`workers/${agentId}`), {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });
      if (res.ok) {
        await get().fetchWorkers();
        return true;
      }
      return false;
    } catch {
      return false;
    }
  },

  deleteWorker: async (agentId) => {
    try {
      const res = await fetch(orgApiPath(`workers/${agentId}`), {
        method: "DELETE",
      });
      if (res.ok) {
        await get().fetchWorkers();
        return true;
      }
      return false;
    } catch {
      return false;
    }
  },

  startWorker: async (agentId) => {
    _optimistic(set, get, agentId, "starting");
    try {
      const res = await fetch(orgApiPath(`workers/${agentId}/start`), {
        method: "POST",
      });
      if (res.ok) {
        _optimistic(set, get, agentId, "running");
        return true;
      }
      // Revert on failure
      _optimistic(set, get, agentId, "stopped");
      return false;
    } catch {
      _optimistic(set, get, agentId, "stopped");
      return false;
    }
  },

  stopWorker: async (agentId) => {
    _optimistic(set, get, agentId, "stopping");
    try {
      const res = await fetch(orgApiPath(`workers/${agentId}/stop`), {
        method: "POST",
      });
      if (res.ok) {
        _optimistic(set, get, agentId, "stopped");
        return true;
      }
      _optimistic(set, get, agentId, "running");
      return false;
    } catch {
      _optimistic(set, get, agentId, "running");
      return false;
    }
  },

  pauseWorker: async (agentId) => {
    _optimistic(set, get, agentId, "paused");
    try {
      const res = await fetch(orgApiPath(`workers/${agentId}/pause`), {
        method: "POST",
      });
      if (res.ok) return true;
      _optimistic(set, get, agentId, "running");
      return false;
    } catch {
      _optimistic(set, get, agentId, "running");
      return false;
    }
  },

  resumeWorker: async (agentId) => {
    _optimistic(set, get, agentId, "running");
    try {
      const res = await fetch(orgApiPath(`workers/${agentId}/resume`), {
        method: "POST",
      });
      if (res.ok) return true;
      _optimistic(set, get, agentId, "paused");
      return false;
    } catch {
      _optimistic(set, get, agentId, "paused");
      return false;
    }
  },

  fetchLogs: async (agentId) => {
    try {
      const res = await fetch(orgApiPath(`workers/${agentId}/logs`));
      if (!res.ok) return [];
      const data = await res.json();
      return data.lines || [];
    } catch {
      return [];
    }
  },

  reset: () => set({
    createdAgentId: null,
    creating: false,
  }),
}));
