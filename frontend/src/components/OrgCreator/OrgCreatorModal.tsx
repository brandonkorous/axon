import { useEffect, useRef, useState } from "react";
import { useOrgStore, OrgTemplate } from "../../stores/orgStore";

const TEMPLATE_ICONS: Record<string, string> = {
  rocket: "\u{1F680}",
  home: "\u{1F3E0}",
  briefcase: "\u{1F4BC}",
  palette: "\u{1F3A8}",
  "graduation-cap": "\u{1F393}",
};

interface OrgCreatorModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function OrgCreatorModal({ isOpen, onClose }: OrgCreatorModalProps) {
  const { templates, fetchTemplates, createOrg, setActiveOrg } = useOrgStore();
  const [selectedTemplate, setSelectedTemplate] = useState<OrgTemplate | null>(null);
  const [orgName, setOrgName] = useState("");
  const [orgId, setOrgId] = useState("");
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState("");
  const dialogRef = useRef<HTMLDialogElement>(null);

  useEffect(() => {
    if (isOpen) {
      if (templates.length === 0) fetchTemplates();
      dialogRef.current?.showModal();
    } else {
      dialogRef.current?.close();
    }
  }, [isOpen, templates.length, fetchTemplates]);

  const handleNameChange = (name: string) => {
    setOrgName(name);
    setOrgId(name.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, ""));
    setError("");
  };

  const handleCreate = async () => {
    if (!orgName.trim() || !orgId.trim()) return;
    setCreating(true);
    setError("");

    const result = await createOrg(orgId, orgName, selectedTemplate?.id);
    if (result) {
      setActiveOrg(result.id);
      setOrgName("");
      setOrgId("");
      setSelectedTemplate(null);
      onClose();
      window.location.reload();
    } else {
      setError("Could not create organization. An organization with this name may already exist.");
    }
    setCreating(false);
  };

  return (
    <dialog ref={dialogRef} className="modal" onClose={onClose}>
      <div className="modal-box max-w-2xl max-h-[85vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-semibold text-base-content">Create Organization</h3>
          <form method="dialog">
            <button className="btn btn-ghost btn-sm btn-square" aria-label="Close">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} className="w-5 h-5">
                <path d="M18 6L6 18M6 6l12 12" />
              </svg>
            </button>
          </form>
        </div>

        <div className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-base-content/80 mb-3">
              Choose a template
            </label>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
              {templates.map((t) => (
                <button
                  key={t.id}
                  onClick={() => setSelectedTemplate(selectedTemplate?.id === t.id ? null : t)}
                  className={`text-left p-4 rounded-xl border transition-all ${
                    selectedTemplate?.id === t.id
                      ? "border-primary bg-primary/10"
                      : "border-secondary/50 bg-base-300/30 hover:border-neutral-content/30 hover:bg-base-300/50"
                  }`}
                >
                  <div className="text-2xl mb-2">
                    {TEMPLATE_ICONS[t.icon] || "\u{2B50}"}
                  </div>
                  <div className="text-sm font-semibold text-base-content">{t.name}</div>
                  <div className="text-[11px] text-base-content/60 mt-1 line-clamp-2">
                    {t.description}
                  </div>
                </button>
              ))}

              <button
                onClick={() => setSelectedTemplate(null)}
                className={`text-left p-4 rounded-xl border transition-all ${
                  selectedTemplate === null
                    ? "border-primary bg-primary/10"
                    : "border-secondary/50 bg-base-300/30 hover:border-neutral-content/30 hover:bg-base-300/50"
                }`}
              >
                <div className="text-2xl mb-2">+</div>
                <div className="text-sm font-semibold text-base-content">Custom</div>
                <div className="text-[11px] text-base-content/60 mt-1">
                  Start blank, add your own agents
                </div>
              </button>
            </div>
          </div>

          {selectedTemplate && selectedTemplate.agents.length > 0 && (
            <div className="card card-border bg-base-300/30">
              <div className="card-body p-4">
                <div className="text-xs font-medium text-base-content/60 mb-3 uppercase tracking-wider">
                  Included Advisors
                </div>
                <div className="flex flex-wrap gap-2">
                  {selectedTemplate.agents.map((p) => (
                    <div
                      key={p.id}
                      className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-base-300/50"
                    >
                      <span
                        className="w-2 h-2 rounded-full"
                        style={{ backgroundColor: p.color }}
                      />
                      <span className="text-sm text-base-content font-medium">{p.name}</span>
                      <span className="text-[11px] text-base-content/60">{p.title}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-base-content/80 mb-2">
              Organization name
            </label>
            <input
              type="text"
              value={orgName}
              onChange={(e) => handleNameChange(e.target.value)}
              placeholder="e.g. Smith Family, My Startup, Job Search 2026"
              className="input w-full"
              autoFocus
            />
            {orgId && (
              <div className="mt-1.5 text-[11px] text-base-content/60">
                ID: <span className="font-mono text-base-content/60/80">{orgId}</span>
              </div>
            )}
            {error && (
              <div className="mt-1.5 text-[11px] text-error">{error}</div>
            )}
          </div>

          <div className="modal-action">
            <button onClick={onClose} className="btn btn-ghost btn-sm">Cancel</button>
            <button
              onClick={handleCreate}
              disabled={!orgName.trim() || creating}
              className="btn btn-primary btn-sm"
            >
              {creating ? <><span className="loading loading-spinner loading-xs" /> Creating...</> : "Create"}
            </button>
          </div>
        </div>
      </div>
      <form method="dialog" className="modal-backdrop"><button>close</button></form>
    </dialog>
  );
}
