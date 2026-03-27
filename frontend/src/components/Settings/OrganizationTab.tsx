import { useEffect, useState } from "react";
import { useOrgStore } from "../../stores/orgStore";

const ORG_TYPES = [
  { value: "startup", label: "Startup" },
  { value: "family", label: "Family" },
  { value: "job-hunt", label: "Job Hunt" },
  { value: "creator", label: "Creator" },
  { value: "student", label: "Student" },
  { value: "custom", label: "Custom" },
] as const;

export function OrganizationTab() {
  const { orgs, activeOrgId, updateOrg } = useOrgStore();
  const org = orgs.find((o) => o.id === activeOrgId);
  const [saving, setSaving] = useState(false);

  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [type, setType] = useState("");
  const [requireApproval, setRequireApproval] = useState(true);
  const [emailDomain, setEmailDomain] = useState("");
  const [emailSignature, setEmailSignature] = useState("");
  const [inboundPolling, setInboundPolling] = useState(false);

  useEffect(() => {
    if (!org) return;
    setName(org.name);
    setDescription(org.description);
    setType(org.type);
    setRequireApproval(org.comms.require_approval);
    setEmailDomain(org.comms.email_domain);
    setEmailSignature(org.comms.email_signature);
    setInboundPolling(org.comms.inbound_polling);
  }, [org]);

  if (!org) return <p className="text-sm text-base-content/60">No organization selected.</p>;

  const handleSave = async () => {
    setSaving(true);
    await updateOrg(org.id, {
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
    setSaving(false);
  };

  return (
    <div className="space-y-6">
      <div className="space-y-3">
        <h4 className="text-sm font-semibold">Organization Details</h4>
        <label className="form-control">
          <span className="label-text text-xs mb-1">Name</span>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="input input-sm input-bordered w-full"
          />
        </label>
        <label className="form-control">
          <span className="label-text text-xs mb-1">Description</span>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            rows={2}
            className="textarea textarea-sm textarea-bordered w-full resize-y"
          />
        </label>
        <label className="form-control">
          <span className="label-text text-xs mb-1">Type</span>
          <select
            value={type}
            onChange={(e) => setType(e.target.value)}
            className="select select-sm select-bordered w-full"
          >
            {ORG_TYPES.map((t) => (
              <option key={t.value} value={t.value}>{t.label}</option>
            ))}
          </select>
        </label>
      </div>

      <div className="divider my-0" />

      <div className="space-y-3">
        <h4 className="text-sm font-semibold">Communications</h4>
        <ToggleRow
          label="Require approval"
          description="Outbound messages need manual approval before sending"
          checked={requireApproval}
          onChange={setRequireApproval}
        />
        <ToggleRow
          label="Inbound polling"
          description="Automatically check for incoming emails"
          checked={inboundPolling}
          onChange={setInboundPolling}
        />
        <label className="form-control">
          <span className="label-text text-xs mb-1">Email domain</span>
          <input
            type="text"
            value={emailDomain}
            onChange={(e) => setEmailDomain(e.target.value)}
            placeholder="e.g. axon.yourcompany.com"
            className="input input-sm input-bordered w-full font-mono"
          />
        </label>
        <label className="form-control">
          <span className="label-text text-xs mb-1">Email signature</span>
          <textarea
            value={emailSignature}
            onChange={(e) => setEmailSignature(e.target.value)}
            rows={3}
            placeholder="HTML or plain text appended to outbound emails"
            className="textarea textarea-sm textarea-bordered w-full resize-y font-mono text-xs"
          />
        </label>
      </div>

      <button onClick={handleSave} disabled={saving} className="btn btn-primary btn-sm">
        {saving ? <span className="loading loading-spinner loading-xs" /> : "Save Changes"}
      </button>
    </div>
  );
}

function ToggleRow({
  label,
  description,
  checked,
  onChange,
}: {
  label: string;
  description: string;
  checked: boolean;
  onChange: (v: boolean) => void;
}) {
  return (
    <label className="flex items-center justify-between gap-3 cursor-pointer">
      <div>
        <span className="text-sm">{label}</span>
        <p className="text-xs text-base-content/60 mt-0.5">{description}</p>
      </div>
      <input
        type="checkbox"
        className="toggle toggle-sm toggle-primary"
        checked={checked}
        onChange={(e) => onChange(e.target.checked)}
      />
    </label>
  );
}
