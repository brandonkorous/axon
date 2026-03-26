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
  parent_id?: string;
  model: string;
  status: string;
  lifecycle?: LifecycleState;
  system_prompt?: string;
  email?: string | null;
  comms_enabled?: boolean;
  email_alias?: string;
}

export interface PersonaUpdate {
  name?: string;
  title?: string;
  tagline?: string;
  system_prompt?: string;
  color?: string;
  sparkle_color?: string;
  comms_enabled?: boolean;
  email_alias?: string;
}

interface AgentStore {
  agents: AgentInfo[];
  loading: boolean;
  fetchAgents: () => Promise<void>;
  lifecycleAction: (agentId: string, action: string, body?: object) => Promise<void>;
  updatePersona: (agentId: string, update: PersonaUpdate) => Promise<void>;
  fetchAgentDetail: (agentId: string) => Promise<AgentInfo | null>;
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

  fetchAgentDetail: async (agentId) => {
    try {
      const res = await fetch(orgApiPath(`agents/${agentId}`));
      if (!res.ok) return null;
      return (await res.json()) as AgentInfo;
    } catch {
      return null;
    }
  },

  updatePersona: async (agentId, update) => {
    const res = await fetch(orgApiPath(`agents/${agentId}`), {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(update),
    });
    if (!res.ok) throw new Error("Failed to update persona");
    // Refresh agent list to reflect changes
    const { fetchAgents } = useAgentStore.getState();
    await fetchAgents();
  },

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
