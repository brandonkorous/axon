import { create } from "zustand";
import { orgApiPath } from "./orgStore";

export interface IntegrationInfo {
  name: string;
  description: string;
  required_scopes: string[];
  tool_prefix: string;
  tool_count: number;
  enabled_by: string[];
}

export interface IntegrationDetail {
  name: string;
  description: string;
  required_scopes: string[];
  tool_prefix: string;
  tools: { name: string; description: string }[];
  enabled_by: string[];
}

export interface IntegrationStatus {
  name: string;
  registered: boolean;
  credentials_configured: boolean;
}

interface IntegrationStore {
  integrations: IntegrationInfo[];
  loading: boolean;
  fetchIntegrations: () => Promise<void>;
  fetchIntegrationDetail: (name: string) => Promise<IntegrationDetail | null>;
  fetchIntegrationStatus: (name: string) => Promise<IntegrationStatus | null>;
  enableIntegration: (agentId: string, name: string) => Promise<boolean>;
  disableIntegration: (agentId: string, name: string) => Promise<boolean>;
}

export const useIntegrationStore = create<IntegrationStore>((set, get) => ({
  integrations: [],
  loading: false,

  fetchIntegrations: async () => {
    set({ loading: true });
    try {
      const res = await fetch(orgApiPath("integrations"));
      if (!res.ok) throw new Error();
      const data = await res.json();
      set({ integrations: data, loading: false });
    } catch {
      set({ loading: false });
    }
  },

  fetchIntegrationDetail: async (name) => {
    try {
      const res = await fetch(orgApiPath(`integrations/${name}`));
      if (!res.ok) return null;
      return await res.json();
    } catch {
      return null;
    }
  },

  fetchIntegrationStatus: async (name) => {
    try {
      const res = await fetch(orgApiPath(`integrations/${name}/status`));
      if (!res.ok) return null;
      return await res.json();
    } catch {
      return null;
    }
  },

  enableIntegration: async (agentId, name) => {
    try {
      const res = await fetch(
        orgApiPath(`integrations/agents/${agentId}/${name}/enable`),
        { method: "POST" },
      );
      if (!res.ok) return false;
      await get().fetchIntegrations();
      return true;
    } catch {
      return false;
    }
  },

  disableIntegration: async (agentId, name) => {
    try {
      const res = await fetch(
        orgApiPath(`integrations/agents/${agentId}/${name}/disable`),
        { method: "POST" },
      );
      if (!res.ok) return false;
      await get().fetchIntegrations();
      return true;
    } catch {
      return false;
    }
  },
}));
