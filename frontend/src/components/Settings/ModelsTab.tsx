import { useEffect, useState } from "react";
import { useModelStore } from "../../stores/modelStore";
import { RegisteredModelsList } from "./RegisteredModelsList";
import { AddModelForm, OllamaDiscoverButton } from "./AddModelForm";
import { RoleAssignments } from "./RoleAssignments";

export function ModelsTab() {
  const { loading, fetchModels } = useModelStore();
  const [showAddForm, setShowAddForm] = useState(false);

  useEffect(() => {
    fetchModels();
  }, [fetchModels]);

  if (loading) {
    return (
      <div className="flex items-center gap-2 py-4">
        <span className="loading loading-spinner loading-sm" />
        <span className="text-xs text-base-content/60">Loading models...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h4 className="text-sm font-semibold">Registered Models</h4>
          <div className="flex gap-2">
            {!showAddForm && (
              <button
                onClick={() => setShowAddForm(true)}
                className="btn btn-primary btn-sm"
              >
                Add Model
              </button>
            )}
          </div>
        </div>

        {showAddForm && (
          <AddModelForm onClose={() => setShowAddForm(false)} />
        )}

        <RegisteredModelsList />
        <OllamaDiscoverButton />
      </div>

      <div className="divider my-0" />

      <RoleAssignments />
    </div>
  );
}
