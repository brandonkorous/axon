import { useEffect, useRef, useState } from "react";
import { useModels, useModelStatus } from "../../hooks/useModels";
import { RegisteredModelsList } from "./RegisteredModelsList";
import { AddModelForm, OllamaDiscoverButton } from "./AddModelForm";
import { RoleAssignments } from "./RoleAssignments";

export function ModelOnboardingModal({ onClose }: { onClose: () => void }) {
  const { data, isLoading: loading } = useModels();
  const { refetch: refetchStatus } = useModelStatus();
  const dialogRef = useRef<HTMLDialogElement>(null);
  const [showAddForm, setShowAddForm] = useState(false);

  const models = data?.registered_models ?? [];
  const roles = data?.roles ?? { navigator: "", reasoning: "", memory: "", agent: "" };

  useEffect(() => {
    dialogRef.current?.showModal();
  }, []);

  const hasModels = models.length > 0;
  const hasRoles = !!(roles.navigator && roles.reasoning && roles.memory && roles.agent);
  const canFinish = hasModels && hasRoles;

  const handleDone = async () => {
    if (!canFinish) return;
    await refetchStatus();
    dialogRef.current?.close();
    onClose();
  };

  // Prevent closing via Escape when not configured
  const handleCancel = (e: React.SyntheticEvent) => {
    if (!canFinish) e.preventDefault();
  };

  return (
    <dialog
      ref={dialogRef}
      className="modal"
      onCancel={handleCancel}
    >
      <div className="modal-box max-w-2xl max-h-[85vh] bg-base-200 border border-neutral">
        <h3 className="text-lg font-semibold mb-1">Set Up Your Models</h3>
        <p className="text-sm text-base-content/60 mb-4">
          Register at least one model and assign roles to get started.
        </p>

        {loading ? (
          <div className="flex items-center gap-2 py-4">
            <span className="loading loading-spinner loading-sm" />
            <span className="text-xs text-base-content/60">Loading...</span>
          </div>
        ) : (
          <div className="space-y-6">
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <h4 className="text-sm font-semibold">Registered Models</h4>
                {!showAddForm && (
                  <button
                    onClick={() => setShowAddForm(true)}
                    className="btn btn-primary btn-sm"
                  >
                    Add Model
                  </button>
                )}
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
        )}

        <div className="modal-action">
          {!canFinish && (
            <span className="text-xs text-warning mr-auto self-center">
              {!hasModels
                ? "Register at least one model to continue."
                : "Assign all four roles to continue."}
            </span>
          )}
          <button
            onClick={handleDone}
            disabled={!canFinish}
            className="btn btn-primary btn-sm"
          >
            Done
          </button>
        </div>
      </div>
    </dialog>
  );
}
