import { create } from "zustand";
import { orgApiPath } from "./orgStore";

export interface SkillInfo {
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
}

export interface SkillDetail extends SkillInfo {
  tools: { name: string; description: string }[];
  python_deps: string[];
  agents_using: string[];
}

interface SkillStore {
  skills: SkillInfo[];
  loading: boolean;
  selectedSkill: SkillDetail | null;

  fetchSkills: () => Promise<void>;
  fetchSkillDetail: (name: string) => Promise<void>;
  enableSkill: (skillName: string, agentId: string) => Promise<boolean>;
  disableSkill: (skillName: string, agentId: string) => Promise<boolean>;
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
}));
