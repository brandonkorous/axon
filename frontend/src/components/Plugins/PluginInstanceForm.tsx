import { useState, useEffect } from "react";
import { usePluginStore, type PluginInstanceInfo } from "../../stores/pluginStore";
import { useHostAgentStore } from "../../stores/hostAgentStore";
import { useSandboxStore } from "../../stores/sandboxStore";

const DEFAULT_SANDBOX_IMAGE = "code";

export function PluginInstanceForm({
  pluginName,
  instance,
  agents,
  onSave,
  onCancel,
}: {
  pluginName: string;
  instance?: PluginInstanceInfo;
  agents: { id: string; name: string }[];
  onSave: () => void;
  onCancel: () => void;
}) {
  const { createInstance, updateInstance } = usePluginStore();
  const hostAgents = useHostAgentStore((s) => s.agents);
  const fetchHostAgents = useHostAgentStore((s) => s.fetchAgents);
  const sandboxImages = useSandboxStore((s) => s.images);
  const fetchImages = useSandboxStore((s) => s.fetchImages);

  const isEdit = !!instance;
  const [id, setId] = useState(instance?.id || "");
  const [name, setName] = useState(instance?.name || "");
  const [path, setPath] = useState((instance?.config.path as string) || "");
  const [image, setImage] = useState(
    (instance?.config.image as string) || DEFAULT_SANDBOX_IMAGE,
  );
  const [executables, setExecutables] = useState(
    Array.isArray(instance?.config.executables)
      ? (instance.config.executables as string[]).join(", ")
      : "",
  );
  const [hostAgentId, setHostAgentId] = useState(
    (instance?.config.host_agent_id as string) || "",
  );
  const [selectedAgents, setSelectedAgents] = useState<string[]>(
    instance?.agents || [],
  );
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (hostAgents.length === 0) fetchHostAgents();
    if (pluginName === "sandbox" && sandboxImages.length === 0) fetchImages();
  }, [hostAgents.length, fetchHostAgents, pluginName, sandboxImages.length, fetchImages]);

  const toggleAgent = (agentId: string) => {
    setSelectedAgents((prev) =>
      prev.includes(agentId) ? prev.filter((a) => a !== agentId) : [...prev, agentId],
    );
  };

  const handleSave = async () => {
    setSaving(true);
    const execList = executables
      .split(",")
      .map((e) => e.trim())
      .filter(Boolean);
    const selectedHA = hostAgents.find((ha) => ha.id === hostAgentId);
    const hostAgentUrl = selectedHA
      ? `http://host.docker.internal:${selectedHA.port}`
      : "";

    const config: Record<string, unknown> = {
      path,
      executables: execList,
    };
    if (pluginName === "sandbox") {
      config.image = image;
    }
    if (pluginName === "shell_access") {
      config.host_agent_id = hostAgentId || null;
      config.host_agent_url = hostAgentUrl || null;
    }

    let ok: boolean;
    if (isEdit) {
      ok = await updateInstance(pluginName, instance.id, {
        name,
        agents: selectedAgents,
        config,
      });
    } else {
      ok = await createInstance(pluginName, {
        id,
        name: name || id.replace(/-/g, " ").replace(/\b\w/g, (c) => c.toUpperCase()),
        agents: selectedAgents,
        config,
      });
    }
    setSaving(false);
    if (ok) onSave();
  };

  return (
    <div className="bg-base-200 rounded-lg p-4 space-y-3 border border-primary/20">
      <p className="text-xs font-semibold text-primary">
        {isEdit ? `Edit: ${instance.name || instance.id}` : "New Instance"}
      </p>

      {!isEdit && (
        <div className="form-control">
          <label className="label py-0.5">
            <span className="label-text text-xs">ID (slug)</span>
          </label>
          <input
            type="text"
            className="input input-bordered input-sm w-full"
            placeholder="my-workspace"
            value={id}
            onChange={(e) => setId(e.target.value.toLowerCase().replace(/[^a-z0-9-]/g, "-"))}
          />
        </div>
      )}

      <div className="form-control">
        <label className="label py-0.5">
          <span className="label-text text-xs">Display Name</span>
        </label>
        <input
          type="text"
          className="input input-bordered input-sm w-full"
          placeholder="My Workspace"
          value={name}
          onChange={(e) => setName(e.target.value)}
        />
      </div>

      {pluginName === "sandbox" && (
        <div className="form-control">
          <label className="label py-0.5">
            <span className="label-text text-xs">Sandbox Image</span>
          </label>
          <select
            className="select select-bordered select-sm w-full"
            value={image}
            onChange={(e) => setImage(e.target.value)}
          >
            {sandboxImages
              .filter((img) => img.status === "ready")
              .map((img) => (
                <option key={img.type} value={img.type}>
                  {img.type} — {img.description}
                </option>
              ))}
            {sandboxImages
              .filter((img) => img.status !== "ready")
              .map((img) => (
                <option key={img.type} value={img.type} disabled>
                  {img.type} — {img.description} (not built)
                </option>
              ))}
          </select>
        </div>
      )}

      {pluginName === "shell_access" && (
        <div className="form-control">
          <label className="label py-0.5">
            <span className="label-text text-xs">Host Agent</span>
          </label>
          <select
            className="select select-bordered select-sm w-full"
            value={hostAgentId}
            onChange={(e) => setHostAgentId(e.target.value)}
          >
            <option value="">None (direct execution)</option>
            {hostAgents.map((ha) => (
              <option key={ha.id} value={ha.id}>
                {ha.name} ({ha.path}) — :{ha.port}{" "}
                {ha.status === "running" ? "\u{1F7E2}" : "\u{1F534}"}
              </option>
            ))}
          </select>
        </div>
      )}

      <div className="form-control">
        <label className="label py-0.5">
          <span className="label-text text-xs">Path</span>
        </label>
        <input
          type="text"
          className="input input-bordered input-sm w-full"
          placeholder={pluginName === "sandbox" ? "Empty = no mount (agent creates files inside)" : "/path/to/directory"}
          value={path}
          onChange={(e) => setPath(e.target.value)}
        />
      </div>

      <div className="form-control">
        <label className="label py-0.5">
          <span className="label-text text-xs">Executables (comma-separated)</span>
        </label>
        <input
          type="text"
          className="input input-bordered input-sm w-full"
          placeholder="git, node, python"
          value={executables}
          onChange={(e) => setExecutables(e.target.value)}
        />
      </div>

      {/* Agent assignment */}
      <div className="form-control">
        <label className="label py-0.5">
          <span className="label-text text-xs">Agents with access</span>
        </label>
        <div className="flex flex-wrap gap-2 mt-1">
          {agents
            .filter((a) => a.id !== "huddle")
            .map((a) => (
              <label key={a.id} className="flex items-center gap-1.5 cursor-pointer">
                <input
                  type="checkbox"
                  className="checkbox checkbox-xs checkbox-primary"
                  checked={selectedAgents.includes(a.id)}
                  onChange={() => toggleAgent(a.id)}
                />
                <span className="text-xs">{a.name}</span>
              </label>
            ))}
        </div>
      </div>

      <div className="flex gap-2 pt-1">
        <button
          onClick={handleSave}
          disabled={saving || (!isEdit && !id)}
          className="btn btn-primary btn-sm"
        >
          {saving ? <span className="loading loading-spinner loading-xs" /> : isEdit ? "Save" : "Create"}
        </button>
        <button onClick={onCancel} className="btn btn-ghost btn-sm">
          Cancel
        </button>
      </div>
    </div>
  );
}
