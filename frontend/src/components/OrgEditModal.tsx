import { useEffect, useRef, useState } from "react";
import { useOrgStore, OrgInfo } from "../stores/orgStore";
import { CredentialManager } from "./Credentials/CredentialManager";

const ORG_TYPES = [
  { value: "custom", label: "Custom" },
  { value: "startup", label: "Startup" },
  { value: "family", label: "Family" },
  { value: "job-hunt", label: "Job Hunt" },
  { value: "creator", label: "Creator" },
  { value: "student", label: "Student" },
] as const;

interface OrgEditModalProps {
  isOpen: boolean;
  onClose: () => void;
  org: OrgInfo;
}

export function OrgEditModal({ isOpen, onClose, org }: OrgEditModalProps) {
  const { updateOrg } = useOrgStore();
  const [name, setName] = useState(org.name);
  const [description, setDescription] = useState(org.description);
  const [type, setType] = useState(org.type);
  const [requireApproval, setRequireApproval] = useState(org.comms?.require_approval ?? true);
  const [emailDomain, setEmailDomain] = useState(org.comms?.email_domain ?? "");
  const [emailSignature, setEmailSignature] = useState(org.comms?.email_signature ?? "");
  const [inboundPolling, setInboundPolling] = useState(org.comms?.inbound_polling ?? false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const dialogRef = useRef<HTMLDialogElement>(null);

  useEffect(() => {
    if (isOpen) {
      setName(org.name);
      setDescription(org.description);
      setType(org.type);
      setRequireApproval(org.comms?.require_approval ?? true);
      setEmailDomain(org.comms?.email_domain ?? "");
      setEmailSignature(org.comms?.email_signature ?? "");
      setInboundPolling(org.comms?.inbound_polling ?? false);
      setError("");
      dialogRef.current?.showModal();
    } else {
      dialogRef.current?.close();
    }
  }, [isOpen, org]);

  const hasChanges =
    name !== org.name ||
    description !== org.description ||
    type !== org.type ||
    requireApproval !== (org.comms?.require_approval ?? true) ||
    emailDomain !== (org.comms?.email_domain ?? "") ||
    emailSignature !== (org.comms?.email_signature ?? "") ||
    inboundPolling !== (org.comms?.inbound_polling ?? false);

  const handleSave = async () => {
    if (!name.trim()) return;
    setSaving(true);
    setError("");

    const ok = await updateOrg(org.id, {
      name,
      description,
      type,
      comms: {
        require_approval: requireApproval,
        email_domain: emailDomain,
        email_signature: emailSignature,
        inbound_polling: inboundPolling,
      },
    });
    if (ok) {
      onClose();
    } else {
      setError("Failed to update organization.");
    }
    setSaving(false);
  };

  return (
    <dialog ref={dialogRef} className="modal" onClose={onClose}>
      <div className="modal-box max-w-lg">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-semibold text-base-content">Edit Organization</h3>
          <form method="dialog">
            <button className="btn btn-ghost btn-sm btn-square" aria-label="Close">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} className="w-5 h-5">
                <path d="M18 6L6 18M6 6l12 12" />
              </svg>
            </button>
          </form>
        </div>

        <div className="space-y-4">
          {/* General */}
          <div>
            <label className="block text-sm font-medium text-base-content/80 mb-1.5">Name</label>
            <input
              type="text"
              value={name}
              onChange={(e) => { setName(e.target.value); setError(""); }}
              className="input w-full"
              autoFocus
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-base-content/80 mb-1.5">Description</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={2}
              className="textarea w-full"
              placeholder="What is this organization for?"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-base-content/80 mb-1.5">Type</label>
            <select
              value={type}
              onChange={(e) => setType(e.target.value)}
              className="select w-full"
            >
              {ORG_TYPES.map((t) => (
                <option key={t.value} value={t.value}>{t.label}</option>
              ))}
            </select>
          </div>

          {/* Comms */}
          <div className="divider text-xs text-base-content/60 uppercase tracking-wider my-2">Communications</div>

          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm font-medium text-base-content/80">Require approval</div>
              <div className="text-[11px] text-base-content/60">
                Approve outbound messages before they are sent
              </div>
            </div>
            <input
              type="checkbox"
              className="toggle toggle-sm toggle-primary"
              checked={requireApproval}
              onChange={(e) => setRequireApproval(e.target.checked)}
            />
          </div>

          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm font-medium text-base-content/80">Inbound email polling</div>
              <div className="text-[11px] text-base-content/60">
                Poll for incoming emails (requires Resend inbound support)
              </div>
            </div>
            <input
              type="checkbox"
              className="toggle toggle-sm toggle-primary"
              checked={inboundPolling}
              onChange={(e) => setInboundPolling(e.target.checked)}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-base-content/80 mb-1.5">
              API Credentials
            </label>
            <CredentialManager />
          </div>

          <div>
            <label className="block text-sm font-medium text-base-content/80 mb-1.5">
              Email domain
            </label>
            <input
              type="text"
              value={emailDomain}
              onChange={(e) => setEmailDomain(e.target.value)}
              className="input input-sm w-full"
              placeholder="axon.yourcompany.com"
            />
            <div className="text-[11px] text-base-content/60 mt-1">
              Domain used for outbound agent emails
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-base-content/80 mb-1.5">
              Email signature
            </label>
            <textarea
              value={emailSignature}
              onChange={(e) => setEmailSignature(e.target.value)}
              rows={3}
              className="textarea textarea-sm w-full font-mono text-xs"
              placeholder={"— {{agent_name}} via Axon\nuseaxon.dev"}
            />
            <div className="text-[11px] text-base-content/60 mt-1">
              HTML appended to every outbound email. Use {"{{agent_name}}"} for the sender's name.
            </div>
          </div>

          {/* Footer */}
          <div className="text-[11px] text-base-content/60">
            ID: <span className="font-mono text-base-content/60/80">{org.id}</span>
          </div>

          {error && <div className="text-[11px] text-error">{error}</div>}

          <div className="modal-action">
            <button onClick={onClose} className="btn btn-ghost btn-sm">Cancel</button>
            <button
              onClick={handleSave}
              disabled={!name.trim() || !hasChanges || saving}
              className="btn btn-primary btn-sm"
            >
              {saving ? <><span className="loading loading-spinner loading-xs" /> Saving...</> : "Save"}
            </button>
          </div>
        </div>
      </div>
      <form method="dialog" className="modal-backdrop"><button>close</button></form>
    </dialog>
  );
}
