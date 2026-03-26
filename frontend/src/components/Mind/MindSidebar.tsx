import { useEffect, useRef } from "react";
import type { GraphNode, SearchResult } from "../../stores/mindStore";

interface Agent {
  id: string;
  name: string;
}

interface Props {
  agents: Agent[];
  selectedAgentId: string;
  onAgentChange: (id: string) => void;
  searchQuery: string;
  onSearchChange: (q: string) => void;
  searchResults: SearchResult[];
  nodes: GraphNode[];
  selectedFilePath: string | null;
  visibleBranches: Set<string>;
  onToggleBranch: (branch: string) => void;
  onFileSelect: (path: string) => void;
  stats: { node_count: number; edge_count: number } | null;
}

export function MindSidebar({
  agents,
  selectedAgentId,
  onAgentChange,
  searchQuery,
  onSearchChange,
  searchResults,
  nodes,
  selectedFilePath,
  visibleBranches,
  onToggleBranch,
  onFileSelect,
  stats,
}: Props) {
  const searchRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === "/" && !e.ctrlKey && !e.metaKey) {
        const target = e.target as HTMLElement;
        if (target.tagName === "INPUT" || target.tagName === "TEXTAREA") return;
        e.preventDefault();
        searchRef.current?.focus();
      }
    }
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  const branches = nodes.reduce<Record<string, GraphNode[]>>((acc, node) => {
    const branch = node.branch || "root";
    if (!acc[branch]) acc[branch] = [];
    acc[branch].push(node);
    return acc;
  }, {});

  return (
    <div className="flex flex-col h-full">
      {/* Agent selector */}
      <div className="p-3 border-b border-neutral">
        <select
          value={selectedAgentId}
          onChange={(e) => onAgentChange(e.target.value)}
          aria-label="Select agent vault"
          className="select select-sm w-full"
        >
          {agents
            .filter((a) => a.id !== "axon")
            .map((a) => (
              <option key={a.id} value={a.id}>{a.name}</option>
            ))}
        </select>
      </div>

      {/* Search */}
      <div className="p-3 border-b border-neutral">
        <input
          ref={searchRef}
          type="text"
          value={searchQuery}
          onChange={(e) => onSearchChange(e.target.value)}
          placeholder="Search vault...  (/)"
          aria-label="Search vault"
          className="input input-sm w-full"
        />
      </div>

      {/* Stats */}
      {stats && (
        <div className="px-3 py-2 border-b border-neutral flex gap-3 text-[10px] text-base-content/60">
          <span>{stats.node_count} files</span>
          <span>{stats.edge_count} links</span>
        </div>
      )}

      {/* File list / search results */}
      <div className="flex-1 overflow-y-auto p-2">
        {searchQuery && searchResults.length > 0 ? (
          <div className="space-y-1">
            <p className="px-2 text-xs text-base-content/60">{searchResults.length} results</p>
            {searchResults.map((r) => (
              <button
                key={r.path}
                onClick={() => onFileSelect(r.path)}
                className="w-full text-left px-2 py-1.5 rounded text-sm text-base-content/80 hover:bg-base-300"
              >
                <div className="font-medium">{r.title}</div>
                <div className="text-xs text-base-content/60 truncate">{r.snippet}</div>
              </button>
            ))}
          </div>
        ) : (
          Object.entries(branches)
            .sort(([a], [b]) => a.localeCompare(b))
            .map(([branch, branchNodes]) => (
              <div key={branch} className="mb-3">
                <button
                  onClick={() => onToggleBranch(branch)}
                  className="w-full flex items-center gap-1 px-2 py-1 text-xs font-semibold text-base-content/60 uppercase hover:text-base-content"
                >
                  <span className={`transition-transform ${visibleBranches.has(branch) ? "rotate-90" : ""}`}>
                    &#9654;
                  </span>
                  {branch || "Root"}
                  <span className="text-base-content/50 font-normal ml-auto">
                    {branchNodes.length}
                  </span>
                </button>
                {visibleBranches.has(branch) &&
                  branchNodes
                    .sort((a, b) => a.name.localeCompare(b.name))
                    .map((node) => (
                      <button
                        key={node.id}
                        onClick={() => onFileSelect(node.id)}
                        className={`w-full text-left px-4 py-1 rounded text-sm transition-colors ${
                          selectedFilePath === node.id
                            ? "bg-secondary text-base-content"
                            : "text-base-content/60 hover:text-base-content hover:bg-base-300/50"
                        }`}
                      >
                        {node.title || node.name}
                      </button>
                    ))}
              </div>
            ))
        )}
      </div>
    </div>
  );
}
