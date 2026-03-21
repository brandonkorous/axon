import { create } from "zustand";

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
  model: string;
  status: "idle" | "thinking" | "speaking";
}

interface AgentStore {
  agents: AgentInfo[];
  loading: boolean;
  fetchAgents: () => Promise<void>;
  setAgentStatus: (id: string, status: AgentInfo["status"]) => void;
}

export const useAgentStore = create<AgentStore>((set) => ({
  agents: [],
  loading: true,

  fetchAgents: async () => {
    try {
      const res = await fetch("/api/agents");
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
}));
