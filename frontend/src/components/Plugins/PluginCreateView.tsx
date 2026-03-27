import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { usePluginStore } from "../../stores/pluginStore";
import { TagInput } from "./TagInput";

const CATEGORIES = ["general", "research", "integration", "media", "browser"];

function Hint({ children }: { children: React.ReactNode }) {
  return <p className="text-xs text-base-content/50 mt-1">{children}</p>;
}

export function PluginCreateView() {
  const navigate = useNavigate();
  const { createPlugin } = usePluginStore();

  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [version, setVersion] = useState("1.0.0");
  const [author, setAuthor] = useState("axon");
  const [category, setCategory] = useState("general");
  const [icon, setIcon] = useState("");
  const [autoLoad, setAutoLoad] = useState(false);
  const [triggers, setTriggers] = useState<string[]>([]);
  const [toolPrefix, setToolPrefix] = useState("");
  const [pythonDeps, setPythonDeps] = useState<string[]>([]);
  const [requiredCredentials, setRequiredCredentials] = useState<string[]>([]);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState("");

  const nameValid = /^[a-z][a-z0-9_]*$/.test(name);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim() || !nameValid) return;

    setCreating(true);
    setError("");

    const ok = await createPlugin({
      name,
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
      navigate("/plugins");
    } else {
      setError("Failed to create plugin. Name may already be taken.");
      setCreating(false);
    }
  };

  return (
    <div className="h-full flex flex-col">
      <div className="px-6 py-4 border-b border-neutral">
        <button onClick={() => navigate("/plugins")} className="btn btn-ghost btn-xs mb-2">
          &larr; Back to Plugins
        </button>
        <h1 className="text-xl font-bold text-base-content">New Plugin</h1>
        <p className="text-xs text-base-content/60 mt-1">
          Plugins are modular capability packages that give agents new tools. Creating a plugin
          scaffolds a Python module on disk that you can then customize with your own logic.
        </p>
      </div>

      <div className="flex-1 overflow-y-auto p-6">
        <form onSubmit={handleSubmit} className="max-w-xl mx-auto space-y-6">
          {error && (
            <div className="alert alert-error text-sm">{error}</div>
          )}

          {/* -- Identity -- */}
          <fieldset className="space-y-4">
            <legend className="text-sm font-semibold text-base-content/80">Identity</legend>

            {/* Name */}
            <label className="form-control">
              <span className="label-text text-xs mb-1">Name *</span>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value.toLowerCase().replace(/[^a-z0-9_]/g, ""))}
                placeholder="my_custom_plugin"
                className={`input input-sm input-bordered w-full ${name && !nameValid ? "input-error" : ""}`}
              />
              {name && !nameValid ? (
                <span className="text-xs text-error mt-1">Must start with a letter and contain only lowercase letters, digits, and underscores</span>
              ) : (
                <Hint>
                  Unique identifier for this plugin. Used as the directory name and internal reference.
                  Cannot be changed after creation.
                </Hint>
              )}
            </label>

            {/* Description */}
            <label className="form-control">
              <span className="label-text text-xs mb-1">Description</span>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Search the web and fetch page content for research"
                rows={3}
                className="textarea textarea-sm textarea-bordered w-full resize-y"
              />
              <Hint>
                Explain what the plugin does and when an agent should use it. This is shown
                in the plugin browser and helps agents understand the plugin's purpose.
              </Hint>
            </label>

            {/* Version + Author row */}
            <div className="grid grid-cols-2 gap-3">
              <label className="form-control">
                <span className="label-text text-xs mb-1">Version</span>
                <input
                  type="text"
                  value={version}
                  onChange={(e) => setVersion(e.target.value)}
                  className="input input-sm input-bordered w-full"
                />
                <Hint>Semantic version (e.g. 1.0.0). Track changes to your plugin over time.</Hint>
              </label>
              <label className="form-control">
                <span className="label-text text-xs mb-1">Author</span>
                <input
                  type="text"
                  value={author}
                  onChange={(e) => setAuthor(e.target.value)}
                  className="input input-sm input-bordered w-full"
                />
                <Hint>Who built this plugin. Defaults to "axon".</Hint>
              </label>
            </div>
          </fieldset>

          <div className="divider my-0" />

          {/* -- Appearance -- */}
          <fieldset className="space-y-4">
            <legend className="text-sm font-semibold text-base-content/80">Appearance</legend>

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
                <Hint>Groups the plugin in the browser. Pick the closest match.</Hint>
              </label>
              <label className="form-control">
                <span className="label-text text-xs mb-1">Icon</span>
                <input
                  type="text"
                  value={icon}
                  onChange={(e) => setIcon(e.target.value)}
                  placeholder="search"
                  className="input input-sm input-bordered w-full"
                />
                <Hint>Icon name or emoji shown in the UI.</Hint>
              </label>
            </div>
          </fieldset>

          <div className="divider my-0" />

          {/* -- Tool Configuration -- */}
          <fieldset className="space-y-4">
            <legend className="text-sm font-semibold text-base-content/80">Tool Configuration</legend>

            <label className="form-control">
              <span className="label-text text-xs mb-1">Tool Prefix</span>
              <input
                type="text"
                value={toolPrefix}
                onChange={(e) => setToolPrefix(e.target.value)}
                placeholder="e.g. web_"
                className="input input-sm input-bordered w-full"
              />
              <Hint>
                A prefix added to all tool names from this plugin to avoid collisions.
                For example, a prefix of "web_" would produce tools like "web_search" and "web_fetch".
              </Hint>
            </label>
          </fieldset>

          <div className="divider my-0" />

          {/* -- Activation -- */}
          <fieldset className="space-y-4">
            <legend className="text-sm font-semibold text-base-content/80">Activation</legend>

            <label className="flex items-center gap-3 cursor-pointer">
              <input
                type="checkbox"
                className="toggle toggle-sm toggle-primary"
                checked={autoLoad}
                onChange={(e) => setAutoLoad(e.target.checked)}
              />
              <div>
                <span className="text-sm">Auto-load</span>
                <Hint>
                  When enabled, the plugin's tools are always available to the agent. When off,
                  the plugin only activates when a trigger keyword is detected in the conversation.
                </Hint>
              </div>
            </label>

            <label className="form-control">
              <span className="label-text text-xs mb-1">Trigger Keywords</span>
              <TagInput tags={triggers} onChange={setTriggers} placeholder="Add keyword and press Enter" />
              <Hint>
                Words or phrases that cause this plugin to activate on demand. When an agent
                receives a message containing any of these keywords, the plugin's tools become
                available for that turn. Not needed if auto-load is on.
              </Hint>
            </label>
          </fieldset>

          <div className="divider my-0" />

          {/* -- Dependencies -- */}
          <fieldset className="space-y-4">
            <legend className="text-sm font-semibold text-base-content/80">Dependencies</legend>

            <label className="form-control">
              <span className="label-text text-xs mb-1">Python Dependencies</span>
              <TagInput tags={pythonDeps} onChange={setPythonDeps} placeholder="e.g. httpx" />
              <Hint>
                Python packages this plugin needs to function. These should match PyPI
                package names (e.g. "httpx", "trafilatura", "beautifulsoup4"). You'll need to
                install them in your environment separately.
              </Hint>
            </label>

            <label className="form-control">
              <span className="label-text text-xs mb-1">Required Credentials</span>
              <TagInput tags={requiredCredentials} onChange={setRequiredCredentials} placeholder="e.g. api_key" />
              <Hint>
                Credential keys this plugin needs at runtime (e.g. "openai_api_key",
                "google_oauth"). These are injected into the plugin via its configure() method.
                The plugin won't function correctly without them.
              </Hint>
            </label>
          </fieldset>

          <div className="divider my-0" />

          {/* What happens next */}
          <div className="rounded-lg bg-base-300 border border-neutral p-4 space-y-2">
            <h3 className="text-sm font-semibold text-base-content/80">What happens next?</h3>
            <p className="text-xs text-base-content/60 leading-relaxed">
              Clicking "Create Plugin" scaffolds a plugin directory with a <code className="text-primary">plugin.yaml</code> manifest
              and a starter <code className="text-primary">__init__.py</code> module. The module contains a stub plugin class
              with empty <code className="text-primary">get_tools()</code> and <code className="text-primary">execute()</code> methods
              that you'll customize to define what tools the plugin provides and how they work. Once saved,
              the plugin is immediately registered and available to enable for any agent.
            </p>
          </div>

          {/* Submit */}
          <button
            type="submit"
            disabled={!name.trim() || !nameValid || creating}
            className="btn btn-primary btn-sm w-full"
          >
            {creating ? (
              <span className="loading loading-spinner loading-xs" />
            ) : (
              "Create Plugin"
            )}
          </button>
        </form>
      </div>
    </div>
  );
}
