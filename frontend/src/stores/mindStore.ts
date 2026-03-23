import { create } from "zustand";
import { orgApiPath } from "./orgStore";

export interface GraphNode {
  id: string;
  name: string;
  branch: string;
  title: string;
  description: string;
  linkCount: number;
  backlinkCount: number;
  tags: string[];
}

export interface GraphEdge {
  source: string;
  target: string;
  context: string;
}

export interface FileData {
  path: string;
  frontmatter: Record<string, unknown>;
  content: string;
  links: string[];
  backlinks: string[];
}

export interface SearchResult {
  path: string;
  title: string;
  snippet: string;
}

export interface GraphStats {
  node_count: number;
  edge_count: number;
  branches: Record<string, number>;
  top_connected: Array<{ path: string; title: string; connections: number }>;
}

interface MindStore {
  // Data
  nodes: GraphNode[];
  edges: GraphEdge[];
  stats: GraphStats | null;
  selectedFile: FileData | null;
  searchQuery: string;
  searchResults: SearchResult[];
  loading: boolean;
  error: boolean;

  // Filters
  visibleBranches: Set<string>;
  highlightedNodeId: string | null;

  // Actions
  fetchGraph: (agentId: string) => Promise<void>;
  fetchStats: (agentId: string) => Promise<void>;
  selectFile: (agentId: string, path: string) => Promise<void>;
  clearSelection: () => void;
  search: (agentId: string, query: string) => Promise<void>;
  setSearchQuery: (query: string) => void;
  saveFile: (
    agentId: string,
    path: string,
    content: string,
    frontmatter: Record<string, unknown>,
  ) => Promise<void>;
  toggleBranch: (branch: string) => void;
  setHighlightedNode: (nodeId: string | null) => void;
  reset: () => void;
}

export const useMindStore = create<MindStore>((set, get) => ({
  nodes: [],
  edges: [],
  stats: null,
  selectedFile: null,
  searchQuery: "",
  searchResults: [],
  loading: false,
  error: false,
  visibleBranches: new Set<string>(),
  highlightedNodeId: null,

  fetchGraph: async (agentId: string) => {
    set({ loading: true, error: false });
    try {
      const res = await fetch(`${orgApiPath("vaults")}/${agentId}/graph`);
      const data = await res.json();
      const nodes: GraphNode[] = data.nodes || [];
      const branches = new Set(nodes.map((n) => n.branch || "root"));
      set({ nodes, edges: data.edges || [], visibleBranches: branches, loading: false });
    } catch {
      set({ error: true, loading: false });
    }
  },

  fetchStats: async (agentId: string) => {
    try {
      const res = await fetch(`${orgApiPath("vaults")}/${agentId}/graph/stats`);
      const data = await res.json();
      set({ stats: data });
    } catch {
      // Non-critical
    }
  },

  selectFile: async (agentId: string, path: string) => {
    try {
      const res = await fetch(`${orgApiPath("vaults")}/${agentId}/files/${path}`);
      const data = await res.json();
      set({ selectedFile: data, highlightedNodeId: path });
    } catch {
      // Ignore
    }
  },

  clearSelection: () => set({ selectedFile: null, highlightedNodeId: null }),

  search: async (agentId: string, query: string) => {
    if (!query) {
      set({ searchResults: [] });
      return;
    }
    try {
      const res = await fetch(
        `${orgApiPath("vaults")}/${agentId}/search?q=${encodeURIComponent(query)}`,
      );
      const data = await res.json();
      set({ searchResults: data.results || [] });
    } catch {
      set({ searchResults: [] });
    }
  },

  setSearchQuery: (query: string) => set({ searchQuery: query }),

  saveFile: async (agentId, path, content, frontmatter) => {
    await fetch(`${orgApiPath("vaults")}/${agentId}/files/${path}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ content, frontmatter }),
    });
    // Reload file and refresh graph
    await get().selectFile(agentId, path);
    await get().fetchGraph(agentId);
  },

  toggleBranch: (branch: string) => {
    const current = get().visibleBranches;
    const next = new Set(current);
    if (next.has(branch)) {
      next.delete(branch);
    } else {
      next.add(branch);
    }
    set({ visibleBranches: next });
  },

  setHighlightedNode: (nodeId: string | null) => set({ highlightedNodeId: nodeId }),

  reset: () =>
    set({
      nodes: [],
      edges: [],
      stats: null,
      selectedFile: null,
      searchQuery: "",
      searchResults: [],
      loading: false,
      error: false,
      visibleBranches: new Set(),
      highlightedNodeId: null,
    }),
}));
