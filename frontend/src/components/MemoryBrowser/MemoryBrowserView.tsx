import { useCallback, useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { useAgentStore } from "../../stores/agentStore";
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

  // Load graph data
  useEffect(() => {
    if (!selectedAgentId) return;
    fetch(`/api/vaults/${selectedAgentId}/graph`)
      .then((r) => r.json())
      .then((data) => {
        setNodes(data.nodes || []);
        setEdges(data.edges || []);
      })
      .catch(() => {});
  }, [selectedAgentId]);

  // Load file
  const loadFile = useCallback(async (path: string) => {
    if (!selectedAgentId) return;
    try {
      const res = await fetch(`/api/vaults/${selectedAgentId}/files/${path}`);
      const data = await res.json();
      setSelectedFile(data);
      setEditing(false);
    } catch {}
  }, [selectedAgentId]);

  // Search
  useEffect(() => {
    if (!searchQuery || !selectedAgentId) {
      setSearchResults([]);
      return;
    }
    const timeout = setTimeout(async () => {
      try {
        const res = await fetch(
          `/api/vaults/${selectedAgentId}/search?q=${encodeURIComponent(searchQuery)}`
        );
        const data = await res.json();
        setSearchResults(data.results || []);
      } catch {}
    }, 300);
    return () => clearTimeout(timeout);
  }, [searchQuery, selectedAgentId]);

  // Save
  const handleSave = async () => {
    if (!selectedFile || !selectedAgentId) return;
    await fetch(`/api/vaults/${selectedAgentId}/files/${selectedFile.path}`, {
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

  // Group nodes by branch
  const branches = nodes.reduce<Record<string, GraphNode[]>>((acc, node) => {
    const branch = node.branch || "root";
    if (!acc[branch]) acc[branch] = [];
    acc[branch].push(node);
    return acc;
  }, {});

  return (
    <div className="flex h-full">
      {/* Left panel: tree view */}
      <div className="w-72 bg-gray-900 border-r border-gray-800 flex flex-col">
        {/* Agent selector */}
        <div className="p-3 border-b border-gray-800">
          <select
            value={selectedAgentId}
            onChange={(e) => {
              setSelectedAgentId(e.target.value);
              setSelectedFile(null);
            }}
            className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-200"
          >
            {agents
              .filter((a) => a.id !== "axon")
              .map((a) => (
                <option key={a.id} value={a.id}>
                  {a.name}
                </option>
              ))}
          </select>
        </div>

        {/* Search */}
        <div className="p-3 border-b border-gray-800">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search vault..."
            className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-200 placeholder-gray-500"
          />
        </div>

        {/* Search results or tree */}
        <div className="flex-1 overflow-y-auto p-2">
          {searchQuery && searchResults.length > 0 ? (
            <div className="space-y-1">
              <p className="px-2 text-xs text-gray-500">{searchResults.length} results</p>
              {searchResults.map((r) => (
                <button
                  key={r.path}
                  onClick={() => loadFile(r.path)}
                  className="w-full text-left px-2 py-1.5 rounded text-sm text-gray-300 hover:bg-gray-800"
                >
                  <div className="font-medium">{r.title}</div>
                  <div className="text-xs text-gray-500 truncate">{r.snippet}</div>
                </button>
              ))}
            </div>
          ) : (
            Object.entries(branches)
              .sort(([a], [b]) => a.localeCompare(b))
              .map(([branch, branchNodes]) => (
                <div key={branch} className="mb-3">
                  <p className="px-2 py-1 text-xs font-semibold text-gray-500 uppercase">
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
                            ? "bg-gray-700 text-white"
                            : "text-gray-400 hover:text-white hover:bg-gray-800/50"
                        }`}
                      >
                        {node.title || node.name}
                        {(node.linkCount + node.backlinkCount) > 2 && (
                          <span className="text-xs text-gray-600 ml-1">
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

      {/* Right panel: file viewer/editor */}
      <div className="flex-1 overflow-y-auto">
        {selectedFile ? (
          <div className="p-6">
            {/* File header */}
            <div className="flex items-center justify-between mb-4">
              <div>
                <h2 className="text-xl font-bold text-white">
                  {(selectedFile.frontmatter.name as string) || selectedFile.path}
                </h2>
                <p className="text-sm text-gray-500">{selectedFile.path}</p>
              </div>
              <div className="flex gap-2">
                {editing ? (
                  <>
                    <button
                      onClick={handleSave}
                      className="px-3 py-1.5 bg-violet-600 hover:bg-violet-500 text-white rounded-lg text-sm"
                    >
                      Save
                    </button>
                    <button
                      onClick={() => setEditing(false)}
                      className="px-3 py-1.5 bg-gray-700 hover:bg-gray-600 text-white rounded-lg text-sm"
                    >
                      Cancel
                    </button>
                  </>
                ) : (
                  <button
                    onClick={() => {
                      setEditing(true);
                      setEditContent(selectedFile.content);
                    }}
                    className="px-3 py-1.5 bg-gray-700 hover:bg-gray-600 text-white rounded-lg text-sm"
                  >
                    Edit
                  </button>
                )}
              </div>
            </div>

            {/* Frontmatter */}
            {Object.keys(selectedFile.frontmatter).length > 0 && (
              <div className="bg-gray-800/30 border border-gray-700/30 rounded-lg p-3 mb-4 text-sm">
                {Object.entries(selectedFile.frontmatter).map(([key, value]) => (
                  <div key={key} className="flex gap-2">
                    <span className="text-gray-500">{key}:</span>
                    <span className="text-gray-300">{String(value)}</span>
                  </div>
                ))}
              </div>
            )}

            {/* Content */}
            {editing ? (
              <textarea
                value={editContent}
                onChange={(e) => setEditContent(e.target.value)}
                className="w-full h-96 bg-gray-800 border border-gray-700 rounded-lg p-4 text-sm text-gray-200 font-mono resize-y"
              />
            ) : (
              <div className="prose prose-sm prose-invert max-w-none">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {selectedFile.content}
                </ReactMarkdown>
              </div>
            )}

            {/* Links & Backlinks */}
            {(selectedFile.links.length > 0 || selectedFile.backlinks.length > 0) && (
              <div className="mt-6 grid grid-cols-2 gap-4">
                {selectedFile.links.length > 0 && (
                  <div>
                    <h3 className="text-sm font-semibold text-gray-400 mb-2">
                      Links ({selectedFile.links.length})
                    </h3>
                    <div className="space-y-1">
                      {selectedFile.links.map((link) => (
                        <button
                          key={link}
                          onClick={() => loadFile(link)}
                          className="block text-sm text-violet-400 hover:text-violet-300"
                        >
                          {link}
                        </button>
                      ))}
                    </div>
                  </div>
                )}
                {selectedFile.backlinks.length > 0 && (
                  <div>
                    <h3 className="text-sm font-semibold text-gray-400 mb-2">
                      Backlinks ({selectedFile.backlinks.length})
                    </h3>
                    <div className="space-y-1">
                      {selectedFile.backlinks.map((link) => (
                        <button
                          key={link}
                          onClick={() => loadFile(link)}
                          className="block text-sm text-violet-400 hover:text-violet-300"
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
          <div className="flex items-center justify-center h-full text-gray-500">
            Select a file to view
          </div>
        )}
      </div>
    </div>
  );
}
