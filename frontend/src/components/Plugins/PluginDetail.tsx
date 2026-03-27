import { useEffect, useState } from "react";
import { usePluginStore } from "../../stores/pluginStore";
import { useAgentStore } from "../../stores/agentStore";
import { TagInput } from "./TagInput";

const CATEGORIES = ["general", "research", "integration", "media", "browser"];

export function PluginDetail({ pluginName, onBack }: { pluginName: string; onBack: () => void }) {
  const { selectedPlugin, fetchPluginDetail, enablePlugin, disablePlugin, updatePlugin, deletePlugin } =
    usePluginStore();
  const { agents } = useAgentStore();

  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [deleting, setDeleting] = useState(false);

  // Edit form state
  const [description, setDescription] = useState("");
  const [version, setVersion] = useState("");
  const [author, setAuthor] = useState("");
  const [category, setCategory] = useState("general");
  const [icon, setIcon] = useState("");
  const [autoLoad, setAutoLoad] = useState(false);
  const [triggers, setTriggers] = useState<string[]>([]);
  const [toolPrefix, setToolPrefix] = useState("");
  const [pythonDeps, setPythonDeps] = useState<string[]>([]);
  const [requiredCredentials, setRequiredCredentials] = useState<string[]>([]);

  useEffect(() => {
    fetchPluginDetail(pluginName);
  }, [pluginName, fetchPluginDetail]);

  // Sync edit form when selectedPlugin loads
  useEffect(() => {
    if (selectedPlugin) {
      setDescription(selectedPlugin.description);
      setVersion(selectedPlugin.version);
      setAuthor(selectedPlugin.author);
      setCategory(selectedPlugin.category);
      setIcon(selectedPlugin.icon);
      setAutoLoad(selectedPlugin.auto_load);
      setTriggers(selectedPlugin.triggers);
      setToolPrefix("");
      setPythonDeps(selectedPlugin.python_deps || []);
      setRequiredCredentials(selectedPlugin.required_credentials || []);
    }
  }, [selectedPlugin]);

  if (!selectedPlugin) {
    return (
      <div className="flex items-center justify-center h-32">
        <span className="loading loading-spinner loading-md text-primary" />
      </div>
    );
  }

  const s = selectedPlugin;

  const handleToggle = async (agentId: string) => {
    const isUsing = s.agents_using.includes(agentId);
    const ok = isUsing
      ? await disablePlugin(pluginName, agentId)
      : await enablePlugin(pluginName, agentId);
    if (ok) fetchPluginDetail(pluginName);
  };

  const handleSave = async () => {
    setSaving(true);
    const ok = await updatePlugin(pluginName, {
      description,
      version,
      author,
      category,
      icon,
      auto_load: autoLoad,
      triggers,
      tool_prefix: toolPrefix,
      python_deps: pythonDeps,
      required_credentials: requiredCredentials,
    });
    if (ok) {
      await fetchPluginDetail(pluginName);
      setEditing(false);
    }
    setSaving(false);
  };

  const handleDelete = async () => {
    setDeleting(true);
    const result = await deletePlugin(pluginName);
    if (result.deleted) {
      onBack();
    }
    setDeleting(false);
  };

  const cancelEdit = () => {
    setEditing(false);
    // Reset to current values
    setDescription(s.description);
    setVersion(s.version);
    setAuthor(s.author);
    setCategory(s.category);
    setIcon(s.icon);
    setAutoLoad(s.auto_load);
    setTriggers(s.triggers);
    setPythonDeps(s.python_deps || []);
    setRequiredCredentials(s.required_credentials || []);
  };

  return (
    <div className="h-full flex flex-col">
      <div className="px-6 py-4 border-b border-neutral">
        <button onClick={onBack} className="btn btn-ghost btn-xs mb-2">
          &larr; Back to Plugins
        </button>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <h1 className="text-xl font-bold text-base-content">{s.name}</h1>
            <span className="badge badge-sm badge-ghost">v{s.version}</span>
            {s.is_builtin && <span className="badge badge-sm badge-ghost">built-in</span>}
            {s.auto_load && <span className="badge badge-sm badge-accent">auto-load</span>}
          </div>
          {!s.is_builtin && !editing && (
            <button onClick={() => setEditing(true)} className="btn btn-ghost btn-sm">
              Edit
            </button>
          )}
          {editing && (
            <div className="flex gap-2">
              <button onClick={cancelEdit} className="btn btn-ghost btn-sm">
                Cancel
              </button>
              <button onClick={handleSave} disabled={saving} className="btn btn-primary btn-sm">
                {saving ? <span className="loading loading-spinner loading-xs" /> : "Save"}
              </button>
            </div>
          )}
        </div>
        {!editing && <p className="text-xs text-base-content/60 mt-1">{s.description}</p>}
      </div>

      <div className="flex-1 overflow-y-auto p-6">
        <div className="max-w-xl mx-auto space-y-6">
          {editing ? (
            <EditForm
              description={description}
              setDescription={setDescription}
              version={version}
              setVersion={setVersion}
              author={author}
              setAuthor={setAuthor}
              category={category}
              setCategory={setCategory}
              icon={icon}
              setIcon={setIcon}
              autoLoad={autoLoad}
              setAutoLoad={setAutoLoad}
              triggers={triggers}
              setTriggers={setTriggers}
              toolPrefix={toolPrefix}
              setToolPrefix={setToolPrefix}
              pythonDeps={pythonDeps}
              setPythonDeps={setPythonDeps}
              requiredCredentials={requiredCredentials}
              setRequiredCredentials={setRequiredCredentials}
            />
          ) : (
            <ViewMode
              plugin={s}
              agents={agents}
              onToggle={handleToggle}
            />
          )}

          {/* Danger Zone — external plugins only */}
          {!s.is_builtin && !editing && (
            <div className="border border-error/30 rounded-lg p-4 space-y-3">
              <h3 className="text-sm font-semibold text-error">Danger Zone</h3>
              <p className="text-xs text-base-content/60">
                Permanently remove this plugin and its files. It will be disabled for all agents.
              </p>
              {!confirmDelete ? (
                <button
                  onClick={() => setConfirmDelete(true)}
                  className="btn btn-error btn-sm btn-outline"
                >
                  Remove Plugin
                </button>
              ) : (
                <span className="flex items-center gap-2">
                  <span className="text-xs text-error">Are you sure?</span>
                  <button onClick={handleDelete} disabled={deleting} className="btn btn-error btn-xs">
                    {deleting ? <span className="loading loading-spinner loading-xs" /> : "Yes, delete"}
                  </button>
                  <button onClick={() => setConfirmDelete(false)} className="btn btn-ghost btn-xs">
                    No
                  </button>
                </span>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}


// ---------------------------------------------------------------------------
// View mode (read-only sections)
// ---------------------------------------------------------------------------

function ViewMode({
  plugin: s,
  agents,
  onToggle,
}: {
  plugin: any;
  agents: any[];
  onToggle: (agentId: string) => void;
}) {
  return (
    <>
      {/* Tools */}
      <Section title="Tools">
        <div className="space-y-1.5">
          {s.tools.map((t: any) => (
            <div key={typeof t === "string" ? t : t.name} className="flex items-start gap-2">
              <code className="text-xs font-mono text-primary shrink-0">
                {typeof t === "string" ? t : t.name}
              </code>
              {typeof t !== "string" && t.description && (
                <span className="text-xs text-base-content/60">{t.description}</span>
              )}
            </div>
          ))}
        </div>
      </Section>

      {/* Triggers */}
      {s.triggers.length > 0 && (
        <Section title="Trigger Keywords">
          <div className="flex flex-wrap gap-1.5">
            {s.triggers.map((t: string) => (
              <span key={t} className="badge badge-sm badge-outline">{t}</span>
            ))}
          </div>
        </Section>
      )}

      {/* Agent Enablement */}
      <Section title="Enabled For">
        <div className="space-y-2">
          {agents
            .filter((a) => a.id !== "huddle")
            .map((a) => {
              const enabled = s.agents_using.includes(a.id);
              return (
                <label key={a.id} className="flex items-center gap-3 cursor-pointer">
                  <input
                    type="checkbox"
                    className="toggle toggle-sm toggle-primary"
                    checked={enabled}
                    onChange={() => onToggle(a.id)}
                  />
                  <span className="text-sm">{a.name}</span>
                </label>
              );
            })}
        </div>
      </Section>

      {/* Dependencies */}
      {s.python_deps?.length > 0 && (
        <Section title="Python Dependencies">
          <div className="flex flex-wrap gap-1.5">
            {s.python_deps.map((d: string) => (
              <code key={d} className="text-xs font-mono badge badge-sm badge-ghost">{d}</code>
            ))}
          </div>
        </Section>
      )}

      {/* Credentials */}
      {s.required_credentials?.length > 0 && (
        <Section title="Required Credentials">
          <div className="flex flex-wrap gap-1.5">
            {s.required_credentials.map((c: string) => (
              <span key={c} className="badge badge-sm badge-warning badge-outline">{c}</span>
            ))}
          </div>
        </Section>
      )}

      {/* Metadata */}
      <Section title="Info">
        <div className="grid grid-cols-2 gap-2 text-xs text-base-content/60">
          <span>Author</span><span className="text-base-content">{s.author}</span>
          <span>Category</span><span className="text-base-content">{s.category}</span>
          <span>Version</span><span className="text-base-content">{s.version}</span>
        </div>
      </Section>
    </>
  );
}


// ---------------------------------------------------------------------------
// Edit form (inline fields)
// ---------------------------------------------------------------------------

function EditForm({
  description, setDescription,
  version, setVersion,
  author, setAuthor,
  category, setCategory,
  icon, setIcon,
  autoLoad, setAutoLoad,
  triggers, setTriggers,
  toolPrefix, setToolPrefix,
  pythonDeps, setPythonDeps,
  requiredCredentials, setRequiredCredentials,
}: {
  description: string; setDescription: (v: string) => void;
  version: string; setVersion: (v: string) => void;
  author: string; setAuthor: (v: string) => void;
  category: string; setCategory: (v: string) => void;
  icon: string; setIcon: (v: string) => void;
  autoLoad: boolean; setAutoLoad: (v: boolean) => void;
  triggers: string[]; setTriggers: (v: string[]) => void;
  toolPrefix: string; setToolPrefix: (v: string) => void;
  pythonDeps: string[]; setPythonDeps: (v: string[]) => void;
  requiredCredentials: string[]; setRequiredCredentials: (v: string[]) => void;
}) {
  return (
    <div className="space-y-5">
      <label className="form-control">
        <span className="label-text text-xs mb-1">Description</span>
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          rows={3}
          className="textarea textarea-sm textarea-bordered w-full resize-y"
        />
      </label>

      <div className="grid grid-cols-2 gap-3">
        <label className="form-control">
          <span className="label-text text-xs mb-1">Version</span>
          <input
            type="text"
            value={version}
            onChange={(e) => setVersion(e.target.value)}
            className="input input-sm input-bordered w-full"
          />
        </label>
        <label className="form-control">
          <span className="label-text text-xs mb-1">Author</span>
          <input
            type="text"
            value={author}
            onChange={(e) => setAuthor(e.target.value)}
            className="input input-sm input-bordered w-full"
          />
        </label>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <label className="form-control">
          <span className="label-text text-xs mb-1">Category</span>
          <select
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            className="select select-sm select-bordered w-full"
          >
            {CATEGORIES.map((c) => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>
        </label>
        <label className="form-control">
          <span className="label-text text-xs mb-1">Icon</span>
          <input
            type="text"
            value={icon}
            onChange={(e) => setIcon(e.target.value)}
            className="input input-sm input-bordered w-full"
          />
        </label>
      </div>

      <label className="form-control">
        <span className="label-text text-xs mb-1">Tool Prefix</span>
        <input
          type="text"
          value={toolPrefix}
          onChange={(e) => setToolPrefix(e.target.value)}
          className="input input-sm input-bordered w-full"
        />
      </label>

      <label className="flex items-center gap-3 cursor-pointer">
        <input
          type="checkbox"
          className="toggle toggle-sm toggle-primary"
          checked={autoLoad}
          onChange={(e) => setAutoLoad(e.target.checked)}
        />
        <div>
          <span className="text-sm">Auto-load</span>
          <p className="text-xs text-base-content/60">Always active when enabled for an agent</p>
        </div>
      </label>

      <label className="form-control">
        <span className="label-text text-xs mb-1">Trigger Keywords</span>
        <TagInput tags={triggers} onChange={setTriggers} placeholder="Add keyword and press Enter" />
      </label>

      <label className="form-control">
        <span className="label-text text-xs mb-1">Python Dependencies</span>
        <TagInput tags={pythonDeps} onChange={setPythonDeps} placeholder="e.g. httpx" />
      </label>

      <label className="form-control">
        <span className="label-text text-xs mb-1">Required Credentials</span>
        <TagInput tags={requiredCredentials} onChange={setRequiredCredentials} placeholder="e.g. api_key" />
      </label>
    </div>
  );
}


function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div>
      <h3 className="text-sm font-semibold text-base-content/80 mb-2">{title}</h3>
      {children}
    </div>
  );
}
