import { create } from "zustand";

export interface OrgInfo {
  id: string;
  name: string;
  description: string;
  type: string;
  agent_count: number;
  has_huddle: boolean;
}

export interface OrgTemplatePersona {
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
  personas: OrgTemplatePersona[];
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
  createOrg: (id: string, name: string, template?: string) => Promise<OrgInfo | null>;
}

const STORAGE_KEY = "axon-active-org";

export const useOrgStore = create<OrgStore>((set, get) => ({
  orgs: [],
  activeOrgId: localStorage.getItem(STORAGE_KEY) || "default",
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
        orgs.find((o) => o.id === currentId)?.id || orgs[0]?.id || "default";

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
        const err = await res.json();
        throw new Error(err.detail || "Failed to create organization");
      }
      // Refresh orgs list
      await get().fetchOrgs();
      const newOrg = get().orgs.find((o) => o.id === id) || null;
      return newOrg;
    } catch {
      return null;
    }
  },
}));

/**
 * Build an org-scoped API path.
 * If multi-org is active, returns /api/orgs/{orgId}/{path}
 * Otherwise returns /api/{path} (legacy route).
 */
export function orgApiPath(path: string): string {
  const { isMultiOrg, activeOrgId } = useOrgStore.getState();
  if (isMultiOrg) {
    return `/api/orgs/${activeOrgId}/${path}`;
  }
  return `/api/${path}`;
}

/**
 * Build an org-scoped WebSocket path segment.
 */
export function orgWsPath(path: string): string {
  const { isMultiOrg, activeOrgId } = useOrgStore.getState();
  if (isMultiOrg) {
    return `/api/orgs/${activeOrgId}/${path}`;
  }
  return `/api/${path}`;
}
