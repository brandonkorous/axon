import { create } from "zustand";
import { orgApiPath } from "./orgStore";

export interface LifecycleState {
  agent_id: string;
  status: "active" | "paused" | "disabled" | "terminated";
  strategy_override: string | null;
  rate_limit: { max_per_minute: number };
  paused_at: number | null;
  terminated_at: number | null;
  queued_messages: number;
}

export interface AgentInfo {
  id: string;
  name: string;
  title: string;
  tagline: string;
  ui: {
    color: string;
    avatar: string;
    sparkle_color: string;
  };
  type: "advisor" | "orchestrator" | "huddle" | "external";
  model: string;
  status: string;
  lifecycle?: LifecycleState;
}

interface AgentStore {
  agents: AgentInfo[];
  loading: boolean;
  fetchAgents: () => Promise<void>;
  setAgentStatus: (id: string, status: AgentInfo["status"]) => void;
  lifecycleAction: (agentId: string, action: string, body?: object) => Promise<void>;
}

export const useAgentStore = create<AgentStore>((set) => ({
  agents: [],
  loading: true,

  fetchAgents: async () => {
    try {
      const res = await fetch(orgApiPath("agents"));
      const data = await res.json();
      set({ agents: data.agents, loading: false });
    } catch {
      set({ loading: false });
    }
  },

  setAgentStatus: (id, status) =>
    set((state) => ({
      agents: state.agents.map((a) => (a.id === id ? { ...a, status } : a)),
    })),

  lifecycleAction: async (agentId, action, body) => {
    const opts: RequestInit = { method: action === "strategy-override-clear" ? "DELETE" : "POST" };
    let path = `lifecycle/${agentId}/${action}`;
    if (action === "strategy-override-clear") {
      path = `lifecycle/${agentId}/strategy-override`;
    }
    if (body) {
      opts.headers = { "Content-Type": "application/json" };
      opts.body = JSON.stringify(body);
    }
    await fetch(orgApiPath(path), opts);
    // Refresh to get updated lifecycle state
    const { fetchAgents } = useAgentStore.getState();
    await fetchAgents();
  },
}));
