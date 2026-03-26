import { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { FileData } from "../../stores/mindStore";

interface Props {
  file: FileData;
  onSave: (content: string, frontmatter: Record<string, unknown>) => void;
  onLinkClick: (path: string) => void;
  onClose: () => void;
}

export function MindFileDetail({ file, onSave, onLinkClick, onClose }: Props) {
  const [editing, setEditing] = useState(false);
  const [editContent, setEditContent] = useState("");

  const handleEdit = () => {
    setEditing(true);
    setEditContent(file.content);
  };

  const handleSave = () => {
    onSave(editContent, file.frontmatter);
    setEditing(false);
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="p-4 border-b border-neutral flex items-start justify-between gap-2">
        <div className="min-w-0">
          <h2 className="text-lg font-bold text-base-content truncate">
            {(file.frontmatter.name as string) || file.path}
          </h2>
          <p className="text-xs text-base-content/60 truncate">{file.path}</p>
        </div>
        <div className="flex gap-1 shrink-0">
          {editing ? (
            <>
              <button onClick={handleSave} className="btn btn-primary btn-xs">Save</button>
              <button onClick={() => setEditing(false)} className="btn btn-ghost btn-xs">Cancel</button>
            </>
          ) : (
            <button onClick={handleEdit} className="btn btn-ghost btn-xs">Edit</button>
          )}
          <button onClick={onClose} className="btn btn-ghost btn-xs" aria-label="Close detail panel">
            &#10005;
          </button>
        </div>
      </div>

      {/* Body */}
      <div className="flex-1 overflow-y-auto p-4">
        {/* Frontmatter */}
        {Object.keys(file.frontmatter).length > 0 && (
          <div className="card card-border bg-base-300/30 mb-4">
            <div className="card-body p-3 text-sm">
              {Object.entries(file.frontmatter).map(([key, value]) => (
                <div key={key} className="flex gap-2">
                  <span className="text-base-content/60 shrink-0">{key}:</span>
                  <span className="text-base-content/80 truncate">{String(value)}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Content */}
        {editing ? (
          <textarea
            value={editContent}
            onChange={(e) => setEditContent(e.target.value)}
            aria-label="Edit file content"
            className="textarea w-full h-64 font-mono resize-y text-sm"
          />
        ) : (
          <div className="prose prose-sm max-w-none">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {file.content}
            </ReactMarkdown>
          </div>
        )}

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
                      onClick={() => onLinkClick(link)}
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
                      onClick={() => onLinkClick(link)}
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
      </div>
    </div>
  );
}
