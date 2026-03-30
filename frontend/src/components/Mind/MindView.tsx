import { useCallback, useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { useAgentStore } from "../../stores/agentStore";
import { useMindStore } from "../../stores/mindStore";
import { MindGraph } from "./MindGraph";
import { MindSidebar } from "./MindSidebar";
import { MindFileDetail } from "./MindFileDetail";

export function MindView() {
  const { agentId: paramAgentId } = useParams<{ agentId?: string }>();
  const { agents } = useAgentStore();
  const store = useMindStore();

  const [selectedAgentId, setSelectedAgentId] = useState(
    paramAgentId || agents.find((a) => a.id !== "axon")?.id || "",
  );
  const [sidebarOpen, setSidebarOpen] = useState(true);

  // Fetch graph + stats on agent change
  useEffect(() => {
    if (!selectedAgentId) return;
    store.reset();
    store.fetchGraph(selectedAgentId);
    store.fetchStats(selectedAgentId);
  }, [selectedAgentId]);

  // Debounced search
  useEffect(() => {
    if (!selectedAgentId) return;
    const timeout = setTimeout(() => {
      store.search(selectedAgentId, store.searchQuery);
    }, 300);
    return () => clearTimeout(timeout);
  }, [store.searchQuery, selectedAgentId]);

  // Escape to deselect
  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") store.clearSelection();
    }
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  const handleAgentChange = useCallback((id: string) => {
    setSelectedAgentId(id);
    useMindStore.getState().clearSelection();
  }, []);

  const handleFileSelect = useCallback(
    (path: string) => {
      if (selectedAgentId) store.selectFile(selectedAgentId, path);
    },
    [selectedAgentId],
  );

  const handleSave = useCallback(
    (content: string, frontmatter: Record<string, unknown>) => {
      if (selectedAgentId && store.selectedFile) {
        store.saveFile(selectedAgentId, store.selectedFile.path, content, frontmatter);
      }
    },
    [selectedAgentId, store.selectedFile],
  );

  if (store.loading) {
    return (
      <div className="h-full flex items-center justify-center">
        <span className="loading loading-spinner loading-md text-primary" />
      </div>
    );
  }

  if (store.error) {
    return (
      <div className="h-full flex flex-col items-center justify-center gap-2 text-base-content/60">
        <p className="text-error text-sm">Failed to load vault graph.</p>
        <button
          onClick={() => store.fetchGraph(selectedAgentId)}
          className="btn btn-ghost btn-sm text-error"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="flex h-full relative">
      {/* Mobile backdrop */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-20 bg-black/50 md:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <div
        className={`fixed z-30 inset-y-0 left-0 w-64 bg-base-200 border-r border-neutral flex flex-col transition-transform duration-200 md:static md:translate-x-0 ${
          sidebarOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <MindSidebar
          agents={agents}
          selectedAgentId={selectedAgentId}
          onAgentChange={handleAgentChange}
          searchQuery={store.searchQuery}
          onSearchChange={store.setSearchQuery}
          searchResults={store.searchResults}
          nodes={store.nodes}
          selectedFilePath={store.selectedFile?.path ?? null}
          visibleBranches={store.visibleBranches}
          onToggleBranch={store.toggleBranch}
          onFileSelect={handleFileSelect}
          stats={store.stats}
        />
      </div>

      {/* Graph (center) */}
      <div className="flex-1 min-w-0 relative">
        {/* Mobile menu toggle */}
        <button
          onClick={() => setSidebarOpen(true)}
          className="absolute top-3 left-3 z-10 btn btn-ghost btn-sm btn-square md:hidden"
          aria-label="Open sidebar"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} className="w-5 h-5">
            <path d="M3 12h18M3 6h18M3 18h18" />
          </svg>
        </button>

        <MindGraph
          nodes={store.nodes}
          edges={store.edges}
          visibleBranches={store.visibleBranches}
          highlightedNodeId={store.highlightedNodeId}
          selectedNodeId={store.selectedFile?.path ?? null}
          onNodeSelect={handleFileSelect}
          onNodeHover={store.setHighlightedNode}
        />
      </div>

      {/* Detail panel (right) */}
      {store.selectedFile && (
        <div className="w-96 border-l border-neutral bg-base-200 hidden lg:flex lg:flex-col">
          <MindFileDetail
            file={store.selectedFile}
            onSave={handleSave}
            onLinkClick={handleFileSelect}
            onClose={store.clearSelection}
          />
        </div>
      )}
    </div>
  );
}
