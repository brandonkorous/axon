import { useState } from "react";
import type { PluginInstanceInfo } from "../../hooks/usePlugins";
import { useDeleteInstance } from "../../hooks/usePlugins";
import { PluginInstanceForm } from "./PluginInstanceForm";

export function PluginInstanceList({
  pluginName,
  instances,
  agents,
  onRefresh,
}: {
  pluginName: string;
  instances: PluginInstanceInfo[];
  agents: { id: string; name: string }[];
  onRefresh: () => void;
}) {
  const deleteInstance = useDeleteInstance();
  const [editingId, setEditingId] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const handleDelete = async (id: string) => {
    try {
      await deleteInstance.mutateAsync({ pluginName, instanceId: id });
      setDeletingId(null);
      onRefresh();
    } catch {
      // delete failed
    }
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-base-content/80">Instances</h3>
        {!creating && (
          <button
            onClick={() => setCreating(true)}
            className="btn btn-primary btn-xs"
          >
            + Add Instance
          </button>
        )}
      </div>

      {instances.length === 0 && !creating && (
        <p className="text-xs text-base-content/50 text-center py-4">
          No instances configured. Add one to enable this plugin for agents.
        </p>
      )}

      <div className="space-y-3">
        {instances.map((inst) =>
          editingId === inst.id ? (
            <PluginInstanceForm
              key={inst.id}
              pluginName={pluginName}
              instance={inst}
              agents={agents}
              onSave={() => {
                setEditingId(null);
                onRefresh();
              }}
              onCancel={() => setEditingId(null)}
            />
          ) : (
            <InstanceRow
              key={inst.id}
              instance={inst}
              agents={agents}
              isDeleting={deletingId === inst.id}
              onEdit={() => setEditingId(inst.id)}
              onDelete={() => handleDelete(inst.id)}
              onConfirmDelete={() => setDeletingId(inst.id)}
              onCancelDelete={() => setDeletingId(null)}
            />
          ),
        )}

        {creating && (
          <PluginInstanceForm
            pluginName={pluginName}
            agents={agents}
            onSave={() => {
              setCreating(false);
              onRefresh();
            }}
            onCancel={() => setCreating(false)}
          />
        )}
      </div>
    </div>
  );
}


function InstanceRow({
  instance: inst,
  agents,
  isDeleting,
  onEdit,
  onDelete,
  onConfirmDelete,
  onCancelDelete,
}: {
  instance: PluginInstanceInfo;
  agents: { id: string; name: string }[];
  isDeleting: boolean;
  onEdit: () => void;
  onDelete: () => void;
  onConfirmDelete: () => void;
  onCancelDelete: () => void;
}) {
  const agentNames = inst.agents
    .map((id) => agents.find((a) => a.id === id)?.name || id)
    .join(", ");
  const path = (inst.config.path as string) || "";

  return (
    <div className="bg-base-200 rounded-lg p-3 space-y-1.5">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-base-content">{inst.name || inst.id}</span>
          <span className="badge badge-xs badge-ghost font-mono">{inst.id}</span>
        </div>
        <div className="flex gap-1">
          <button onClick={onEdit} className="btn btn-ghost btn-xs">
            Edit
          </button>
          {!isDeleting ? (
            <button onClick={onConfirmDelete} className="btn btn-ghost btn-xs text-error">
              Delete
            </button>
          ) : (
            <span className="flex items-center gap-1">
              <button onClick={onDelete} className="btn btn-error btn-xs">Yes</button>
              <button onClick={onCancelDelete} className="btn btn-ghost btn-xs">No</button>
            </span>
          )}
        </div>
      </div>

      {path && (
        <p className="text-xs text-base-content/50 font-mono truncate">{path}</p>
      )}
      {!path && (
        <p className="text-xs text-base-content/50 italic">No shared folder — agent works in its own isolated space</p>
      )}

      <div className="flex flex-wrap gap-1">
        {inst.agents.length === 0 && (
          <span className="text-xs text-base-content/40 italic">No agents assigned</span>
        )}
        {inst.agents.map((aid) => (
          <span key={aid} className="badge badge-xs badge-primary badge-outline">
            {agents.find((a) => a.id === aid)?.name || aid}
          </span>
        ))}
      </div>
    </div>
  );
}
