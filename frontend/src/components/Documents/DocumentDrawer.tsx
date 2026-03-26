import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { orgApiPath } from "../../stores/orgStore";
import type { FileData } from "../../stores/mindStore";

interface Props {
  vaultId: string;
  filePath: string;
  onClose: () => void;
  onNavigate?: (filePath: string) => void;
}

export function DocumentDrawer({ vaultId, filePath, onClose, onNavigate }: Props) {
  const [file, setFile] = useState<FileData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);

    const fetchFile = async () => {
      // Try the specified vault first
      const res = await fetch(`${orgApiPath("vaults")}/${vaultId}/files/${filePath}`);
      if (res.ok) return res.json();

      // Fallback: resolve across all vaults in the org
      const resolveRes = await fetch(`${orgApiPath("vaults")}/resolve/${filePath}`);
      if (resolveRes.ok) return resolveRes.json();

      throw new Error(`Document not found (${res.status})`);
    };

    fetchFile()
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
      : filePath.split("/").pop()?.replace(/\.md$/, "") || filePath;

  return (
    <AnimatePresence>
      <motion.div
        className="fixed inset-0 z-50 flex justify-end"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
      >
        {/* Backdrop */}
        <div className="absolute inset-0 bg-black/50" onClick={onClose} />

        {/* Drawer */}
        <motion.div
          className="relative w-full max-w-2xl bg-base-200 border-l border-neutral flex flex-col shadow-2xl"
          initial={{ x: "100%" }}
          animate={{ x: 0 }}
          exit={{ x: "100%" }}
          transition={{ type: "spring", damping: 30, stiffness: 300 }}
        >
          {/* Header */}
          <div className="px-6 py-4 border-b border-neutral flex items-start justify-between gap-3">
            <div className="min-w-0">
              <h2 className="text-lg font-bold text-base-content truncate">{title}</h2>
              <p className="text-xs text-base-content/60 truncate">{filePath}</p>
            </div>
            <button
              onClick={onClose}
              className="btn btn-ghost btn-sm"
              aria-label="Close document"
            >
              ✕
            </button>
          </div>

          {/* Body */}
          <div className="flex-1 overflow-y-auto p-6">
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
                              onClick={() => onNavigate?.(link)}
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
                              onClick={() => onNavigate?.(link)}
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
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}
