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
  title_tag: string;
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
  action_bias?: "proactive" | "balanced" | "deliberative";
  plugins?: {
    shell_access?: {
      enabled: boolean;
      path: string;
      executables: string[];
    };
    sandbox?: {
      enabled: boolean;
      path: string;
      executables: string[];
      image: string;
    };
  };
  plugin_names?: string[];
  runner_status?: "running" | "stopped" | "unknown";
}

export interface PersonaUpdate {
  name?: string;
  title?: string;
  title_tag?: string;
  tagline?: string;
  system_prompt?: string;
  color?: string;
  sparkle_color?: string;
  comms_enabled?: boolean;
  email_alias?: string;
  action_bias?: "proactive" | "balanced" | "deliberative";
}

interface AgentStore {
  agents: AgentInfo[];
  loading: boolean;
  fetchAgents: () => Promise<void>;
  lifecycleAction: (agentId: string, action: string, body?: object) => Promise<void>;
  updatePersona: (agentId: string, update: PersonaUpdate) => Promise<void>;
  fetchAgentDetail: (agentId: string) => Promise<AgentInfo | null>;
  deleteAgent: (agentId: string) => Promise<void>;
  startRunner: (agentId: string) => Promise<void>;
  stopRunner: (agentId: string) => Promise<void>;
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

  deleteAgent: async (agentId) => {
    const res = await fetch(orgApiPath(`lifecycle/${agentId}`), {
      method: "DELETE",
    });
    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      throw new Error(data.detail || "Failed to delete agent");
    }
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

  startRunner: async (agentId) => {
    set((state) => ({
      agents: state.agents.map((a) =>
        a.id === agentId ? { ...a, runner_status: "running" as const } : a,
      ),
    }));
    try {
      await fetch(orgApiPath(`agents/${agentId}/runner/start`), { method: "POST" });
      const { fetchAgents } = useAgentStore.getState();
      await fetchAgents();
    } catch {
      set((state) => ({
        agents: state.agents.map((a) =>
          a.id === agentId ? { ...a, runner_status: "stopped" as const } : a,
        ),
      }));
    }
  },

  stopRunner: async (agentId) => {
    set((state) => ({
      agents: state.agents.map((a) =>
        a.id === agentId ? { ...a, runner_status: "stopped" as const } : a,
      ),
    }));
    try {
      await fetch(orgApiPath(`agents/${agentId}/runner/stop`), { method: "POST" });
      const { fetchAgents } = useAgentStore.getState();
      await fetchAgents();
    } catch {
      set((state) => ({
        agents: state.agents.map((a) =>
          a.id === agentId ? { ...a, runner_status: "running" as const } : a,
        ),
      }));
    }
  },
}));
