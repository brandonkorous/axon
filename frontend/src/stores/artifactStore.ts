import { create } from "zustand";
import { orgApiPath } from "./orgStore";

export interface ArtifactInfo {
  path: string;
  name: string;
  description: string;
  type: string;
  tags: string[];
  status: string;
  created: string;
}

interface ArtifactStore {
  artifacts: ArtifactInfo[];
  loading: boolean;
  selectedContent: string | null;

  fetchArtifacts: () => Promise<void>;
  fetchArtifactContent: (agentId: string, path: string) => Promise<void>;
}

export const useArtifactStore = create<ArtifactStore>((set) => ({
  artifacts: [],
  loading: false,
  selectedContent: null,

  fetchArtifacts: async () => {
    set({ loading: true });
    try {
      // Search across all agent vaults for research artifacts
      const res = await fetch(orgApiPath("agents"));
      const data = await res.json();
      const agents: { id: string }[] = data.agents || [];

      const allArtifacts: ArtifactInfo[] = [];

      for (const agent of agents) {
        try {
          const searchRes = await fetch(
            orgApiPath(`agents/${agent.id}/vault/search?query=research&branch=research`),
          );
          if (!searchRes.ok) continue;
          const searchData = await searchRes.json();
          const results = searchData.results || [];
          for (const r of results) {
            allArtifacts.push({
              path: r.path,
              name: r.name || r.path,
              description: r.description || "",
              type: r.type || "research",
              tags: r.tags || [],
              status: r.status || "",
              created: r.created || "",
            });
          }
        } catch {
          // Skip agents without research vaults
        }
      }

      set({ artifacts: allArtifacts, loading: false });
    } catch {
      set({ loading: false });
    }
  },

  fetchArtifactContent: async (agentId, path) => {
    try {
      const res = await fetch(orgApiPath(`agents/${agentId}/vault/read?path=${encodeURIComponent(path)}`));
      if (res.ok) {
        const data = await res.json();
        set({ selectedContent: data.content || "" });
      }
    } catch {
      set({ selectedContent: null });
    }
  },
}));
