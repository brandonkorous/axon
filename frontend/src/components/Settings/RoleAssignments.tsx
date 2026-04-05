import { useState } from "react";
import { useModels, useUpdateRoles, type ModelRoles } from "../../hooks/useModels";

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
  const { data } = useModels();
  const updateRoles = useUpdateRoles();
  const models = data?.registered_models ?? [];
  const roles = data?.roles ?? { navigator: "", reasoning: "", memory: "", agent: "" };
  const [draft, setDraft] = useState<ModelRoles>({ ...roles });

  const rolesKey = JSON.stringify(roles);
  const [lastKey, setLastKey] = useState(rolesKey);
  if (rolesKey !== lastKey) {
    setDraft({ ...roles });
    setLastKey(rolesKey);
  }

  const handleSave = async () => {
    await updateRoles.mutateAsync(draft);
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
              <option value="">Choose a model</option>
              {models.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.display_name} ({m.model_type})
                </option>
              ))}
            </select>
          </div>
        ))}
      </div>
      <button onClick={handleSave} disabled={updateRoles.isPending} className="btn btn-primary btn-sm">
        {updateRoles.isPending ? <span className="loading loading-spinner loading-xs" /> : "Save Roles"}
      </button>
    </div>
  );
}
