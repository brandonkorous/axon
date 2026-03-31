import { useState } from "react";
import { useModelStore, ModelRoles } from "../../stores/modelStore";

const ROLES: {
  key: keyof ModelRoles;
  label: string;
  help: string;
}[] = [
  {
    key: "navigator",
    label: "Navigator",
    help: "Tool routing and intent classification. Best with a model good at tool calling.",
  },
  {
    key: "reasoning",
    label: "Reasoning",
    help: "Main agent conversation and complex thinking.",
  },
  {
    key: "memory",
    label: "Memory",
    help: "Vault recall and memory consolidation. Can be a lightweight local model.",
  },
  {
    key: "agent",
    label: "Agent",
    help: "Default model for agent conversations.",
  },
];

export function RoleAssignments() {
  const { models, roles, updateRoles } = useModelStore();
  const [draft, setDraft] = useState<ModelRoles>({ ...roles });
  const [saving, setSaving] = useState(false);

  const rolesKey = JSON.stringify(roles);
  const [lastKey, setLastKey] = useState(rolesKey);
  if (rolesKey !== lastKey) {
    setDraft({ ...roles });
    setLastKey(rolesKey);
  }

  const handleSave = async () => {
    setSaving(true);
    await updateRoles(draft);
    setSaving(false);
  };

  return (
    <div className="space-y-4">
      <h4 className="text-sm font-semibold">Role Assignments</h4>
      <div className="grid gap-4">
        {ROLES.map(({ key, label, help }) => (
          <div key={key}>
            <div className="flex items-baseline justify-between mb-1.5">
              <span className="text-sm font-medium">{label}</span>
              <span className="text-xs text-base-content/50">{help}</span>
            </div>
            <select
              value={draft[key]}
              onChange={(e) => setDraft({ ...draft, [key]: e.target.value })}
              className="select select-sm select-bordered w-full"
            >
              <option value="">-- Select model --</option>
              {models.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.display_name} ({m.model_type})
                </option>
              ))}
            </select>
          </div>
        ))}
      </div>
      <button onClick={handleSave} disabled={saving} className="btn btn-primary btn-sm">
        {saving ? <span className="loading loading-spinner loading-xs" /> : "Save Roles"}
      </button>
    </div>
  );
}
