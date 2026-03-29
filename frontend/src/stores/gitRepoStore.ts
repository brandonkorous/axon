import { create } from "zustand";
import { orgApiPath } from "./orgStore";

export type CloneStrategy = "shallow" | "full" | "sparse";

export interface GitRepo {
  id: string;
  org_id: string;
  url: string;
  name: string;
  default_branch: string;
  auth_credential_id: string | null;
  clone_strategy: CloneStrategy;
  sparse_paths: string[];
  created_at: string;
  updated_at: string;
}

export interface GitRepoCreateData {
  url: string;
  name: string;
  default_branch?: string;
  auth_credential_id?: string | null;
  clone_strategy?: CloneStrategy;
  sparse_paths?: string[];
}

interface GitRepoStore {
  repos: GitRepo[];
  loading: boolean;
  fetchRepos: () => Promise<void>;
  createRepo: (data: GitRepoCreateData) => Promise<GitRepo | null>;
  updateRepo: (repoId: string, data: Partial<GitRepoCreateData>) => Promise<boolean>;
  deleteRepo: (repoId: string) => Promise<boolean>;
}

export const useGitRepoStore = create<GitRepoStore>((set, get) => ({
  repos: [],
  loading: false,

  fetchRepos: async () => {
    const hadRepos = get().repos.length > 0;
    if (!hadRepos) set({ loading: true });
    try {
      const res = await fetch(orgApiPath("git-repos"));
      const data = await res.json();
      set({ repos: data.repos || [], loading: false });
    } catch {
      set({ loading: false });
    }
  },

  createRepo: async (data) => {
    try {
      const res = await fetch(orgApiPath("git-repos"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });
      if (!res.ok) return null;
      const repo = await res.json();
      await get().fetchRepos();
      return repo;
    } catch {
      return null;
    }
  },

  updateRepo: async (repoId, data) => {
    try {
      const res = await fetch(orgApiPath(`git-repos/${repoId}`), {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });
      if (!res.ok) return false;
      await get().fetchRepos();
      return true;
    } catch {
      return false;
    }
  },

  deleteRepo: async (repoId) => {
    try {
      const res = await fetch(orgApiPath(`git-repos/${repoId}`), {
        method: "DELETE",
      });
      if (!res.ok) return false;
      await get().fetchRepos();
      return true;
    } catch {
      return false;
    }
  },
}));
