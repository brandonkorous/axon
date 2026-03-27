import { create } from "zustand";
import { orgApiPath } from "./orgStore";

export interface SkillInfo {
  name: string;
  description: string;
  version: string;
  author: string;
  category: string;
  icon: string;
  triggers: string[];
  auto_inject: boolean;
  is_builtin: boolean;
  methodology_preview: string;
}

export interface SkillDetail extends SkillInfo {
  methodology: string;
  agents_using: string[];
}

export interface SkillCreatePayload {
  name: string;
  description?: string;
  version?: string;
  author?: string;
  category?: string;
  icon?: string;
  triggers?: string[];
  auto_inject?: boolean;
  methodology?: string;
}

interface SkillStore {
  skills: SkillInfo[];
  loading: boolean;
  selectedSkill: SkillDetail | null;

  fetchSkills: () => Promise<void>;
  fetchSkillDetail: (name: string) => Promise<void>;
  enableSkill: (skillName: string, agentId: string) => Promise<boolean>;
  disableSkill: (skillName: string, agentId: string) => Promise<boolean>;
  createSkill: (data: SkillCreatePayload) => Promise<boolean>;
  updateSkill: (name: string, data: Partial<SkillCreatePayload>) => Promise<boolean>;
  deleteSkill: (name: string) => Promise<{ deleted: boolean; agents_affected: string[] }>;
}

export const useSkillStore = create<SkillStore>((set) => ({
  skills: [],
  loading: false,
  selectedSkill: null,

  fetchSkills: async () => {
    set({ loading: true });
    try {
      const res = await fetch(orgApiPath("skills"));
      const data = await res.json();
      set({ skills: data.skills || [], loading: false });
    } catch {
      set({ loading: false });
    }
  },

  fetchSkillDetail: async (name) => {
    try {
      const res = await fetch(orgApiPath(`skills/${name}`));
      if (res.ok) {
        const data = await res.json();
        set({ selectedSkill: data });
      }
    } catch {
      // ignore
    }
  },

  enableSkill: async (skillName, agentId) => {
    try {
      const res = await fetch(orgApiPath(`skills/${skillName}/enable`), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ agent_id: agentId }),
      });
      return res.ok;
    } catch {
      return false;
    }
  },

  disableSkill: async (skillName, agentId) => {
    try {
      const res = await fetch(orgApiPath(`skills/${skillName}/disable`), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ agent_id: agentId }),
      });
      return res.ok;
    } catch {
      return false;
    }
  },

  createSkill: async (data) => {
    try {
      const res = await fetch(orgApiPath("skills"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });
      return res.ok;
    } catch {
      return false;
    }
  },

  updateSkill: async (name, data) => {
    try {
      const res = await fetch(orgApiPath(`skills/${name}`), {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });
      return res.ok;
    } catch {
      return false;
    }
  },

  deleteSkill: async (name) => {
    try {
      const res = await fetch(orgApiPath(`skills/${name}`), {
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
}));
