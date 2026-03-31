import { useCallback, useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { useAgentStore } from "../../stores/agentStore";
import { orgApiPath } from "../../stores/orgStore";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface GraphNode {
  id: string;
  name: string;
  branch: string;
  title: string;
  description: string;
  linkCount: number;
  backlinkCount: number;
  tags: string[];
}

interface GraphEdge {
  source: string;
  target: string;
  context: string;
}

interface FileData {
  path: string;
  frontmatter: Record<string, unknown>;
  content: string;
  links: string[];
  backlinks: string[];
}

export function MemoryBrowserView() {
  const { agentId: paramAgentId } = useParams<{ agentId?: string }>();
  const { agents } = useAgentStore();

  const [selectedAgentId, setSelectedAgentId] = useState(
    paramAgentId || agents.find((a) => a.id !== "axon")?.id || ""
  );
  const [nodes, setNodes] = useState<GraphNode[]>([]);
  const [edges, setEdges] = useState<GraphEdge[]>([]);
  const [selectedFile, setSelectedFile] = useState<FileData | null>(null);
  const [editing, setEditing] = useState(false);
  const [editContent, setEditContent] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<Array<{ path: string; title: string; snippet: string }>>([]);
  const [error, setError] = useState(false);

  useEffect(() => {
    if (!selectedAgentId) return;
    setError(false);
    fetch(`${orgApiPath("vaults")}/${selectedAgentId}/graph`)
      .then((r) => r.json())
      .then((data) => {
        setNodes(data.nodes || []);
        setEdges(data.edges || []);
      })
      .catch(() => setError(true));
  }, [selectedAgentId]);

  const loadFile = useCallback(async (path: string) => {
    if (!selectedAgentId) return;
    try {
      const res = await fetch(`${orgApiPath("vaults")}/${selectedAgentId}/files/${path}`);
      const data = await res.json();
      setSelectedFile(data);
      setEditing(false);
      setSidebarOpen(false);
    } catch {}
  }, [selectedAgentId]);

  useEffect(() => {
    if (!searchQuery || !selectedAgentId) {
      setSearchResults([]);
      return;
    }
    const timeout = setTimeout(async () => {
      try {
        const res = await fetch(
          `${orgApiPath("vaults")}/${selectedAgentId}/search?q=${encodeURIComponent(searchQuery)}`
        );
        const data = await res.json();
        setSearchResults(data.results || []);
      } catch {}
    }, 300);
    return () => clearTimeout(timeout);
  }, [searchQuery, selectedAgentId]);

  const handleSave = async () => {
    if (!selectedFile || !selectedAgentId) return;
    await fetch(`${orgApiPath("vaults")}/${selectedAgentId}/files/${selectedFile.path}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        content: editContent,
        frontmatter: selectedFile.frontmatter,
      }),
    });
    setEditing(false);
    loadFile(selectedFile.path);
  };

  const branches = nodes.reduce<Record<string, GraphNode[]>>((acc, node) => {
    const branch = node.branch || "root";
    if (!acc[branch]) acc[branch] = [];
    acc[branch].push(node);
    return acc;
  }, {});

  const [sidebarOpen, setSidebarOpen] = useState(true);

  return (
    <div className="flex h-full relative">
      {/* Mobile backdrop */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-20 bg-black/50 md:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}
      <div className={`fixed z-30 inset-y-0 left-0 w-72 bg-base-200 border-r border-neutral flex flex-col transition-transform duration-200 md:static md:translate-x-0 ${sidebarOpen ? "translate-x-0" : "-translate-x-full"}`}>
        <div className="p-3 border-b border-neutral">
          <select
            value={selectedAgentId}
            onChange={(e) => {
              setSelectedAgentId(e.target.value);
              setSelectedFile(null);
            }}
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

        <div className="p-3 border-b border-neutral">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search vault..."
            aria-label="Search vault"
            className="input input-sm w-full"
          />
        </div>

        <div className="flex-1 overflow-y-auto p-2">
          {error ? (
            <div className="p-3 text-center">
              <p className="text-error text-xs mb-1">Could not load vault. Check your connection and try again.</p>
              <button onClick={() => { setError(false); fetch(`${orgApiPath("vaults")}/${selectedAgentId}/graph`).then((r) => r.json()).then((data) => { setNodes(data.nodes || []); setEdges(data.edges || []); }).catch(() => setError(true)); }} className="btn btn-ghost btn-xs text-error">Retry</button>
            </div>
          ) : searchQuery && searchResults.length > 0 ? (
            <div className="space-y-1">
              <p className="px-2 text-xs text-base-content/60">{searchResults.length} results</p>
              {searchResults.map((r) => (
                <button
                  key={r.path}
                  onClick={() => loadFile(r.path)}
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
                  <p className="px-2 py-1 text-xs font-semibold text-base-content/60 uppercase">
                    {branch || "Root"}
                  </p>
                  {branchNodes
                    .sort((a, b) => a.name.localeCompare(b.name))
                    .map((node) => (
                      <button
                        key={node.id}
                        onClick={() => loadFile(node.id)}
                        className={`w-full text-left px-2 py-1 rounded text-sm transition-colors ${
                          selectedFile?.path === node.id
                            ? "bg-secondary text-base-content"
                            : "text-base-content/60 hover:text-base-content hover:bg-base-300/50"
                        }`}
                      >
                        {node.title || node.name}
                        {(node.linkCount + node.backlinkCount) > 2 && (
                          <span className="text-xs text-base-content/50 ml-1">
                            ({node.linkCount + node.backlinkCount})
                          </span>
                        )}
                      </button>
                    ))}
                </div>
              ))
          )}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto">
        {selectedFile ? (
          <div className="p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setSidebarOpen(true)}
                  className="btn btn-ghost btn-sm btn-square md:hidden"
                  aria-label="Open file browser"
                >
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} className="w-5 h-5"><path d="M3 12h18M3 6h18M3 18h18" /></svg>
                </button>
                <div>
                  <h2 className="text-xl font-bold text-base-content">
                    {(selectedFile.frontmatter.name as string) || selectedFile.path}
                  </h2>
                  <p className="text-sm text-base-content/60">{selectedFile.path}</p>
                </div>
              </div>
              <div className="flex gap-2">
                {editing ? (
                  <>
                    <button onClick={handleSave} className="btn btn-primary btn-sm">Save</button>
                    <button onClick={() => setEditing(false)} className="btn btn-ghost btn-sm">Cancel</button>
                  </>
                ) : (
                  <button
                    onClick={() => { setEditing(true); setEditContent(selectedFile.content); }}
                    className="btn btn-ghost btn-sm"
                  >
                    Edit
                  </button>
                )}
              </div>
            </div>

            {Object.keys(selectedFile.frontmatter).length > 0 && (
              <div className="card card-border bg-base-300/30 mb-4">
                <div className="card-body p-3 text-sm">
                  {Object.entries(selectedFile.frontmatter).map(([key, value]) => (
                    <div key={key} className="flex gap-2">
                      <span className="text-base-content/60">{key}:</span>
                      <span className="text-base-content/80">{String(value)}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {editing ? (
              <textarea
                value={editContent}
                onChange={(e) => setEditContent(e.target.value)}
                aria-label="Edit file content"
                className="textarea w-full h-96 font-mono resize-y"
              />
            ) : (
              <div className="prose prose-sm max-w-none">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {selectedFile.content}
                </ReactMarkdown>
              </div>
            )}

            {(selectedFile.links.length > 0 || selectedFile.backlinks.length > 0) && (
              <div className="mt-6 grid grid-cols-2 gap-4">
                {selectedFile.links.length > 0 && (
                  <div>
                    <h3 className="text-sm font-semibold text-base-content/60 mb-2">
                      Links ({selectedFile.links.length})
                    </h3>
                    <div className="space-y-1">
                      {selectedFile.links.map((link) => (
                        <button
                          key={link}
                          onClick={() => loadFile(link)}
                          className="block text-sm link link-accent"
                        >
                          {link}
                        </button>
                      ))}
                    </div>
                  </div>
                )}
                {selectedFile.backlinks.length > 0 && (
                  <div>
                    <h3 className="text-sm font-semibold text-base-content/60 mb-2">
                      Backlinks ({selectedFile.backlinks.length})
                    </h3>
                    <div className="space-y-1">
                      {selectedFile.backlinks.map((link) => (
                        <button
                          key={link}
                          onClick={() => loadFile(link)}
                          className="block text-sm link link-accent"
                        >
                          {link}
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center h-full text-base-content/60 gap-2">
            <button
              onClick={() => setSidebarOpen(true)}
              className="btn btn-ghost btn-sm md:hidden"
            >
              Open file browser
            </button>
            <span>Select a file to view</span>
          </div>
        )}
      </div>
    </div>
  );
}
