import { create } from "zustand";
import { orgApiPath } from "./orgStore";

export interface HostAgent {
  id: string;
  name: string;
  path: string;
  port: number;
  host: string;
  executables: string[];
  status: "running" | "stopped" | "unknown";
}

interface HostAgentStore {
  agents: HostAgent[];
  loading: boolean;
  managerRunning: boolean;
  hostOrgsPath: string;

  fetchAgents: () => Promise<void>;
  fetchManagerStatus: () => Promise<void>;
  registerAgent: (agent: Omit<HostAgent, "status" | "host">) => Promise<boolean>;
  updateAgent: (id: string, update: Partial<HostAgent>) => Promise<boolean>;
  deleteAgent: (id: string) => Promise<boolean>;
  checkHealth: (id: string) => Promise<string>;
  startAgent: (id: string) => Promise<boolean>;
  stopAgent: (id: string) => Promise<boolean>;
  restartAgent: (id: string) => Promise<boolean>;
}

export const useHostAgentStore = create<HostAgentStore>((set, get) => ({
  agents: [],
  loading: false,
  managerRunning: false,
  hostOrgsPath: "",

  fetchManagerStatus: async () => {
    try {
      const res = await fetch(orgApiPath("host-agents/manager-status"));
      if (res.ok) {
        const data = await res.json();
        set({ managerRunning: data.manager_running, hostOrgsPath: data.host_orgs_path || "" });
      }
    } catch {
      set({ managerRunning: false });
    }
  },

  fetchAgents: async () => {
    set({ loading: true });
    try {
      const res = await fetch(orgApiPath("host-agents"));
      const data = await res.json();
      const agents: HostAgent[] = data.host_agents || data.agents || [];
      set({ agents, loading: false });
    } catch {
      set({ loading: false });
    }
  },

  registerAgent: async (agent) => {
    try {
      const res = await fetch(orgApiPath("host-agents"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(agent),
      });
      if (res.ok) {
        await get().fetchAgents();
        return true;
      }
      return false;
    } catch {
      return false;
    }
  },

  updateAgent: async (id, update) => {
    try {
      const res = await fetch(orgApiPath(`host-agents/${id}`), {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(update),
      });
      if (res.ok) {
        await get().fetchAgents();
        return true;
      }
      return false;
    } catch {
      return false;
    }
  },

  deleteAgent: async (id) => {
    try {
      const res = await fetch(orgApiPath(`host-agents/${id}`), {
        method: "DELETE",
      });
      if (res.ok) {
        await get().fetchAgents();
        return true;
      }
      return false;
    } catch {
      return false;
    }
  },

  startAgent: async (id) => {
    try {
      const res = await fetch(orgApiPath(`host-agents/${id}/start`), { method: "POST" });
      if (res.ok) await get().fetchAgents();
      return res.ok;
    } catch {
      return false;
    }
  },

  stopAgent: async (id) => {
    try {
      const res = await fetch(orgApiPath(`host-agents/${id}/stop`), { method: "POST" });
      if (res.ok) await get().fetchAgents();
      return res.ok;
    } catch {
      return false;
    }
  },

  restartAgent: async (id) => {
    try {
      const res = await fetch(orgApiPath(`host-agents/${id}/restart`), { method: "POST" });
      if (res.ok) await get().fetchAgents();
      return res.ok;
    } catch {
      return false;
    }
  },

  checkHealth: async (id) => {
    try {
      const res = await fetch(orgApiPath(`host-agents/${id}/health`));
      if (!res.ok) return "unknown";
      const data = await res.json();
      const status = data.status || "unknown";
      // Update agent status in local state
      set((state) => ({
        agents: state.agents.map((a) =>
          a.id === id ? { ...a, status } : a,
        ),
      }));
      return status;
    } catch {
      return "unknown";
    }
  },
}));
