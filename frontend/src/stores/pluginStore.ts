import { create } from "zustand";
import { useAgentStore } from "./agentStore";
import { orgApiPath } from "./orgStore";

export interface PluginInfo {
  name: string;
  description: string;
  version: string;
  author: string;
  category: string;
  icon: string;
  auto_load: boolean;
  triggers: string[];
  tools: string[];
  required_credentials: string[];
  is_builtin: boolean;
  source: string;
  sandbox_type: string;
}

export interface PluginInstanceInfo {
  id: string;
  plugin: string;
  name: string;
  agents: string[];
  config: Record<string, unknown>;
}

export interface PluginDetail extends Omit<PluginInfo, "tools"> {
  tools: { name: string; description: string }[];
  python_deps: string[];
  agents_using: string[];
  instances: PluginInstanceInfo[];
  sandbox_type: string;
}

export interface PluginCreatePayload {
  name: string;
  description?: string;
  version?: string;
  author?: string;
  category?: string;
  icon?: string;
  auto_load?: boolean;
  triggers?: string[];
  tool_prefix?: string;
  tools?: string[];
  python_deps?: string[];
  required_credentials?: string[];
}

interface PluginStore {
  plugins: PluginInfo[];
  loading: boolean;
  selectedPlugin: PluginDetail | null;

  fetchPlugins: () => Promise<void>;
  fetchPluginDetail: (name: string) => Promise<void>;
  enablePlugin: (pluginName: string, agentId: string) => Promise<boolean>;
  disablePlugin: (pluginName: string, agentId: string) => Promise<boolean>;
  getPluginConfig: (pluginName: string, agentId: string) => Promise<Record<string, unknown>>;
  setPluginConfig: (pluginName: string, agentId: string, config: Record<string, unknown>) => Promise<boolean>;
  createPlugin: (data: PluginCreatePayload) => Promise<boolean>;
  updatePlugin: (name: string, data: Partial<PluginCreatePayload>) => Promise<boolean>;
  deletePlugin: (name: string) => Promise<{ deleted: boolean; agents_affected: string[] }>;

  // Instance CRUD
  createInstance: (pluginName: string, data: { id: string; name?: string; agents?: string[]; config?: Record<string, unknown> }) => Promise<boolean>;
  updateInstance: (pluginName: string, instanceId: string, data: { name?: string; agents?: string[]; config?: Record<string, unknown> }) => Promise<boolean>;
  deleteInstance: (pluginName: string, instanceId: string) => Promise<boolean>;
}

export const usePluginStore = create<PluginStore>((set) => ({
  plugins: [],
  loading: false,
  selectedPlugin: null,

  fetchPlugins: async () => {
    set({ loading: true });
    try {
      const res = await fetch(orgApiPath("plugins"));
      const data = await res.json();
      set({ plugins: data.plugins || [], loading: false });
    } catch {
      set({ loading: false });
    }
  },

  fetchPluginDetail: async (name) => {
    try {
      const res = await fetch(orgApiPath(`plugins/${name}`));
      if (res.ok) {
        const data = await res.json();
        set({ selectedPlugin: data });
      }
    } catch {
      // ignore
    }
  },

  enablePlugin: async (pluginName, agentId) => {
    try {
      const res = await fetch(orgApiPath(`plugins/${pluginName}/enable`), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ agent_id: agentId }),
      });
      if (res.ok) {
        const { fetchAgents } = useAgentStore.getState();
        fetchAgents();
      }
      return res.ok;
    } catch {
      return false;
    }
  },

  disablePlugin: async (pluginName, agentId) => {
    try {
      const res = await fetch(orgApiPath(`plugins/${pluginName}/disable`), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ agent_id: agentId }),
      });
      if (res.ok) {
        const { fetchAgents } = useAgentStore.getState();
        fetchAgents();
      }
      return res.ok;
    } catch {
      return false;
    }
  },

  getPluginConfig: async (pluginName, agentId) => {
    try {
      const res = await fetch(orgApiPath(`plugins/${pluginName}/config/${agentId}`));
      if (!res.ok) return {};
      const data = await res.json();
      return data.config || {};
    } catch {
      return {};
    }
  },

  setPluginConfig: async (pluginName, agentId, config) => {
    try {
      const res = await fetch(orgApiPath(`plugins/${pluginName}/config`), {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ agent_id: agentId, config }),
      });
      return res.ok;
    } catch {
      return false;
    }
  },

  createPlugin: async (data) => {
    try {
      const res = await fetch(orgApiPath("plugins"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });
      return res.ok;
    } catch {
      return false;
    }
  },

  updatePlugin: async (name, data) => {
    try {
      const res = await fetch(orgApiPath(`plugins/${name}`), {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });
      return res.ok;
    } catch {
      return false;
    }
  },

  deletePlugin: async (name) => {
    try {
      const res = await fetch(orgApiPath(`plugins/${name}`), {
        method: "DELETE",
      });
      if (res.ok) {
        const data = await res.json();
        return { deleted: true, agents_affected: data.agents_affected || [] };
      }
      return { deleted: false, agents_affected: [] };
    } catch {
      return { deleted: false, agents_affected: [] };
    }
  },

  createInstance: async (pluginName, data) => {
    try {
      const res = await fetch(orgApiPath(`plugins/${pluginName}/instances`), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });
      return res.ok;
    } catch {
      return false;
    }
  },

  updateInstance: async (pluginName, instanceId, data) => {
    try {
      const res = await fetch(orgApiPath(`plugins/${pluginName}/instances/${instanceId}`), {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });
      return res.ok;
    } catch {
      return false;
    }
  },

  deleteInstance: async (pluginName, instanceId) => {
    try {
      const res = await fetch(orgApiPath(`plugins/${pluginName}/instances/${instanceId}`), {
        method: "DELETE",
      });
      return res.ok;
    } catch {
      return false;
    }
  },
}));
