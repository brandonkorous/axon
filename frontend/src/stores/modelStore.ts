import { create } from "zustand";
import { orgApiPath } from "./orgStore";

export interface RegisteredModel {
  id: string;
  provider: string;
  display_name: string;
  model_type: "cloud" | "local";
}

export interface ModelRoles {
  navigator: string;
  reasoning: string;
  memory: string;
  agent: string;
}

export interface ModelStatus {
  configured: boolean;
  model_count: number;
  roles_assigned: boolean;
}

export interface CatalogModel {
  id: string;
  name: string;
  description: string;
  tier: "recommended" | "premium" | "budget" | "local";
}

export interface CatalogProvider {
  id: string;
  name: string;
  requires_key: boolean;
  models: CatalogModel[];
}

export interface ModelCatalog {
  providers: CatalogProvider[];
}

interface ModelStore {
  models: RegisteredModel[];
  roles: ModelRoles;
  status: ModelStatus | null;
  catalog: ModelCatalog | null;
  loading: boolean;

  fetchModels: () => Promise<void>;
  fetchRoles: () => Promise<void>;
  fetchStatus: () => Promise<void>;
  fetchCatalog: () => Promise<void>;
  registerModel: (model: Omit<RegisteredModel, "provider">) => Promise<boolean>;
  unregisterModel: (modelId: string) => Promise<boolean>;
  updateRoles: (roles: Partial<ModelRoles>) => Promise<boolean>;
  discoverOllamaModels: () => Promise<RegisteredModel[]>;
}

const DEFAULT_ROLES: ModelRoles = {
  navigator: "",
  reasoning: "",
  memory: "",
  agent: "",
};

export const useModelStore = create<ModelStore>((set, get) => ({
  models: [],
  roles: { ...DEFAULT_ROLES },
  status: null,
  catalog: null,
  loading: false,

  fetchModels: async () => {
    set({ loading: true });
    try {
      const res = await fetch(orgApiPath("models"));
      if (!res.ok) throw new Error();
      const data = await res.json();
      set({
        models: data.registered_models || [],
        roles: data.roles || { ...DEFAULT_ROLES },
        loading: false,
      });
    } catch {
      set({ loading: false });
    }
  },

  fetchRoles: async () => {
    try {
      const res = await fetch(orgApiPath("models/roles"));
      if (!res.ok) return;
      const data = await res.json();
      set({ roles: data });
    } catch {
      // non-critical
    }
  },

  fetchStatus: async () => {
    try {
      const res = await fetch(orgApiPath("models/status"));
      if (!res.ok) return;
      const data = await res.json();
      set({ status: data });
    } catch {
      // non-critical
    }
  },

  fetchCatalog: async () => {
    try {
      const res = await fetch(orgApiPath("models/catalog"));
      if (!res.ok) return;
      const data = await res.json();
      set({ catalog: data });
    } catch {
      // non-critical
    }
  },

  registerModel: async (model) => {
    try {
      const res = await fetch(orgApiPath("models"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(model),
      });
      if (!res.ok) return false;
      await get().fetchModels();
      return true;
    } catch {
      return false;
    }
  },

  unregisterModel: async (modelId) => {
    try {
      const res = await fetch(orgApiPath(`models/${encodeURIComponent(modelId)}`), {
        method: "DELETE",
      });
      if (!res.ok) return false;
      await get().fetchModels();
      return true;
    } catch {
      return false;
    }
  },

  updateRoles: async (roles) => {
    try {
      const merged = { ...get().roles, ...roles };
      const res = await fetch(orgApiPath("models/roles"), {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(merged),
      });
      if (!res.ok) return false;
      set({ roles: merged });
      return true;
    } catch {
      return false;
    }
  },

  discoverOllamaModels: async () => {
    try {
      const res = await fetch(orgApiPath("models/discover"));
      if (!res.ok) return [];
      const data = await res.json();
      return (data.models || []).map((m: { id: string; name: string; size: number }) => ({
        id: m.id,
        provider: "ollama",
        display_name: m.name,
        model_type: "local" as const,
      }));
    } catch {
      return [];
    }
  },
}));
