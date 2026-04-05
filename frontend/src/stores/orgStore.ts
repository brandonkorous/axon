import { create } from "zustand";

export interface DiscordConfig {
  guild_id: string;
  channel_mappings: Record<string, string>; // channel_id -> agent_id or "huddle"
}

export interface SlackConfig {
  channel_mappings: Record<string, string>; // channel_id -> agent_id or "huddle"
}

export interface TeamsConfig {
  tenant_id: string;
  channel_mappings: Record<string, string>; // channel_id -> agent_id or "huddle"
}

export interface ZoomConfig {
  channel_mappings: Record<string, string>; // channel_id -> agent_id or "huddle"
}

export interface OrgComms {
  require_approval: boolean;
  email_domain: string;
  email_signature: string;
  inbound_polling: boolean;
  discord: DiscordConfig;
  slack: SlackConfig;
  teams: TeamsConfig;
  zoom: ZoomConfig;
}

export interface OrgAgent {
  id: string;
  name: string;
  title: string;
}

export interface OrgInfo {
  id: string;
  name: string;
  description: string;
  type: string;
  comms: OrgComms;
  agents: OrgAgent[];
  agent_count: number;
  has_huddle: boolean;
}

export interface OrgTemplateAgent {
  id: string;
  name: string;
  title: string;
  tagline: string;
  color: string;
}

export interface OrgTemplate {
  id: string;
  name: string;
  description: string;
  icon: string;
  agents: OrgTemplateAgent[];
}

interface OrgStore {
  orgs: OrgInfo[];
  activeOrgId: string;
  loading: boolean;
  isMultiOrg: boolean;
  templates: OrgTemplate[];
  fetchOrgs: () => Promise<void>;
  fetchTemplates: () => Promise<void>;
  setActiveOrg: (orgId: string) => void;
  createOrg: (id: string, name: string, template?: string) => Promise<OrgInfo | { error: string } | null>;
  updateOrg: (orgId: string, update: {
    name?: string;
    description?: string;
    type?: string;
    comms?: Partial<OrgComms> & { discord?: Partial<DiscordConfig>; slack?: Partial<SlackConfig>; teams?: Partial<TeamsConfig>; zoom?: Partial<ZoomConfig> };
  }) => Promise<boolean>;
}

const STORAGE_KEY = "axon-active-org";

export const useOrgStore = create<OrgStore>((set, get) => ({
  orgs: [],
  activeOrgId: localStorage.getItem(STORAGE_KEY) || "",
  loading: true,
  isMultiOrg: false,
  templates: [],

  fetchOrgs: async () => {
    try {
      const res = await fetch("/api/orgs");
      const data = await res.json();
      const orgs: OrgInfo[] = data.orgs || [];
      const isMultiOrg = orgs.length > 1;

      // If stored org no longer exists, fall back to first org
      const currentId = get().activeOrgId;
      const activeOrgId =
        orgs.find((o) => o.id === currentId)?.id || orgs[0]?.id || "";

      set({ orgs, isMultiOrg, activeOrgId, loading: false });
      localStorage.setItem(STORAGE_KEY, activeOrgId);
    } catch {
      set({ loading: false });
    }
  },

  fetchTemplates: async () => {
    try {
      const res = await fetch("/api/orgs/templates");
      const data = await res.json();
      set({ templates: data.templates || [] });
    } catch {
      // Templates not available — not critical
    }
  },

  setActiveOrg: (orgId: string) => {
    set({ activeOrgId: orgId });
    localStorage.setItem(STORAGE_KEY, orgId);
  },

  createOrg: async (id: string, name: string, template?: string) => {
    try {
      const res = await fetch("/api/orgs", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id, name, template: template || "" }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: "Unknown error" }));
        return { error: err.detail || "Failed to create organization" } as { error: string };
      }
      // Refresh orgs list
      await get().fetchOrgs();
      const newOrg = get().orgs.find((o) => o.id === id) || null;
      return newOrg;
    } catch (e) {
      return { error: e instanceof Error ? e.message : "Network error" } as { error: string };
    }
  },

  updateOrg: async (orgId, update) => {
    try {
      const res = await fetch(`/api/orgs/${orgId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(update),
      });
      if (!res.ok) return false;
      await get().fetchOrgs();
      return true;
    } catch {
      return false;
    }
  },
}));

/**
 * Build an org-scoped API path: /api/orgs/{orgId}/{path}
 */
export function orgApiPath(path: string): string {
  const { activeOrgId } = useOrgStore.getState();
  if (!activeOrgId) {
    throw new Error("No active organization — wait for org store to initialize");
  }
  return `/api/orgs/${activeOrgId}/${path}`;
}

/**
 * Build an org-scoped WebSocket path segment.
 */
export function orgWsPath(path: string): string {
  const { activeOrgId } = useOrgStore.getState();
  return `/api/orgs/${activeOrgId}/${path}`;
}
