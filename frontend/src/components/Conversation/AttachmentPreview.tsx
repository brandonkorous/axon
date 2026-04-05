import type { Attachment } from "../../stores/conversationStore";

interface AttachmentPreviewProps {
  attachments: Attachment[];
  onRemove: (index: number) => void;
  uploading?: boolean;
}

function isImage(type: string): boolean {
  return type.startsWith("image/");
}

function truncateName(name: string, max = 20): string {
  if (name.length <= max) return name;
  const ext = name.lastIndexOf(".");
  if (ext > 0) {
    const base = name.slice(0, ext);
    const extension = name.slice(ext);
    const available = max - extension.length - 1;
    return `${base.slice(0, available)}…${extension}`;
  }
  return `${name.slice(0, max - 1)}…`;
}

function RemoveButton({ onClick }: { onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      className="btn btn-circle btn-xs btn-ghost absolute -top-1 -right-1 bg-base-300/80 hover:bg-error hover:text-error-content"
      aria-label="Remove attachment"
    >
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} className="w-3 h-3">
        <line x1="18" y1="6" x2="6" y2="18" />
        <line x1="6" y1="6" x2="18" y2="18" />
      </svg>
    </button>
  );
}

export function AttachmentPreview({ attachments, onRemove, uploading }: AttachmentPreviewProps) {
  if (attachments.length === 0) return null;

  return (
    <div className="flex flex-wrap gap-2 px-2 py-2 bg-base-300/30 rounded-t-lg">
      {uploading && (
        <div className="absolute inset-0 bg-base-100/40 rounded-t-lg flex items-center justify-center z-10">
          <span className="loading loading-spinner loading-sm text-primary" />
        </div>
      )}
      {attachments.map((att, i) =>
        isImage(att.type) && att.preview ? (
          <div key={`${att.name}-${i}`} className="relative">
            <img
              src={att.preview}
              alt={att.name}
              className="w-12 h-12 rounded-lg object-cover border border-base-300"
            />
            <RemoveButton onClick={() => onRemove(i)} />
          </div>
        ) : (
          <div
            key={`${att.name}-${i}`}
            className="relative flex items-center gap-1.5 bg-base-300/50 rounded-lg px-2.5 py-1.5 pr-6 border border-base-300"
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} className="w-4 h-4 text-base-content/60 shrink-0">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
              <polyline points="14 2 14 8 20 8" />
            </svg>
            <span className="text-xs text-base-content/80">{truncateName(att.name)}</span>
            <RemoveButton onClick={() => onRemove(i)} />
          </div>
        )
      )}
    </div>
  );
}
