import { useEffect, useState } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { orgApiPath } from "../../stores/orgStore";
import { useAgents } from "../../hooks/useAgents";
import type { FileData } from "../../stores/mindStore";

export function DocumentView({ vaultId: propVaultId, path: propPath }: { vaultId?: string; path?: string } = {}) {
  const { vaultId: paramVaultId, "*": paramFilePath } = useParams<{ vaultId: string; "*": string }>();
  const vaultId = propVaultId || paramVaultId;
  const filePath = propPath || paramFilePath;
  const navigate = useNavigate();
  const { data: agents = [] } = useAgents();
  const [file, setFile] = useState<FileData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const agent = agents.find((a) => a.id === vaultId);

  useEffect(() => {
    if (!vaultId || !filePath) return;
    setLoading(true);
    setError(null);
    fetch(`${orgApiPath("vaults")}/${vaultId}/files/${filePath}`)
      .then((res) => {
        if (!res.ok) throw new Error(`Document not found (${res.status})`);
        return res.json();
      })
      .then((data: FileData) => {
        setFile(data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, [vaultId, filePath]);

  const title =
    file && typeof file.frontmatter.name === "string"
      ? file.frontmatter.name
      : filePath?.split("/").pop()?.replace(/\.md$/, "") || "Document";

  const agentName = agent?.name || vaultId || "Agent";

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="border-b border-neutral bg-base-200 px-6 py-4">
        <div className="flex items-center gap-3">
          <Link
            to={agent ? `/agent/${vaultId}` : "/"}
            className="btn btn-ghost btn-sm"
          >
            ← {agentName}
          </Link>
          <div className="min-w-0">
            <h1 className="text-lg font-bold text-base-content truncate">{title}</h1>
            <p className="text-xs text-base-content/60 truncate">{filePath}</p>
          </div>
        </div>
      </div>

      {/* Body */}
      <div className="flex-1 overflow-y-auto p-6 max-w-4xl mx-auto w-full">
        {loading && (
          <div className="flex items-center justify-center py-12">
            <span className="loading loading-spinner loading-md" />
          </div>
        )}

        {error && (
          <div className="alert alert-error">
            <span>{error}</span>
          </div>
        )}

        {file && !loading && (
          <>
            {/* Frontmatter metadata */}
            {Object.keys(file.frontmatter).length > 0 && (
              <div className="card card-border bg-base-300/30 mb-4">
                <div className="card-body p-3 text-sm">
                  {Object.entries(file.frontmatter).map(([key, value]) => (
                    <div key={key} className="flex gap-2">
                      <span className="text-base-content/60 shrink-0">{key}:</span>
                      <span className="text-base-content/80 truncate">
                        {String(value)}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Markdown content */}
            <div className="prose prose-sm max-w-none">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {file.content}
              </ReactMarkdown>
            </div>

            {/* Links / Backlinks */}
            {(file.links.length > 0 || file.backlinks.length > 0) && (
              <div className="mt-6 grid grid-cols-2 gap-4">
                {file.links.length > 0 && (
                  <div>
                    <h3 className="text-xs font-semibold text-base-content/60 mb-2 uppercase">
                      Links ({file.links.length})
                    </h3>
                    <div className="space-y-1">
                      {file.links.map((link) => (
                        <button
                          key={link}
                          onClick={() => navigate(`/docs/${vaultId}/${link}`)}
                          className="block text-sm link link-accent truncate max-w-full"
                        >
                          {link}
                        </button>
                      ))}
                    </div>
                  </div>
                )}
                {file.backlinks.length > 0 && (
                  <div>
                    <h3 className="text-xs font-semibold text-base-content/60 mb-2 uppercase">
                      Backlinks ({file.backlinks.length})
                    </h3>
                    <div className="space-y-1">
                      {file.backlinks.map((link) => (
                        <button
                          key={link}
                          onClick={() => navigate(`/docs/${vaultId}/${link}`)}
                          className="block text-sm link link-accent truncate max-w-full"
                        >
                          {link}
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
