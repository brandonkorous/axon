import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { usePlugins } from "../../hooks/usePlugins";
import type { PluginInfo } from "../../stores/pluginStore";
import { PluginDetail } from "./PluginDetail";

const CATEGORY_LABELS: Record<string, string> = {
  research: "Research",
  integration: "Integrations",
  media: "Media",
  browser: "Browser",
  general: "General",
};

export function PluginBrowser() {
  const navigate = useNavigate();
  const { data: plugins = [], isLoading } = usePlugins();
  const [selectedPlugin, setSelectedPlugin] = useState<string | null>(null);

  if (selectedPlugin) {
    return <PluginDetail pluginName={selectedPlugin} onBack={() => setSelectedPlugin(null)} />;
  }

  const grouped = groupByCategory(plugins);

  return (
    <div className="h-full flex flex-col">
      <div className="px-6 py-4 border-b border-neutral flex items-start justify-between">
        <div>
          <h1 className="text-xl font-bold text-base-content">Plugins</h1>
          <p className="text-xs text-base-content/60 mt-1">
            Capabilities that agents can load on demand
          </p>
        </div>
        <button onClick={() => navigate("/plugins/new")} className="btn btn-primary btn-sm">
          New Plugin
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-6">
        {isLoading && plugins.length === 0 ? (
          <div className="flex items-center justify-center h-32">
            <span className="loading loading-spinner loading-md text-primary" />
          </div>
        ) : plugins.length === 0 ? (
          <p className="text-sm text-base-content/60 text-center mt-12">
            No plugins registered yet
          </p>
        ) : (
          <div className="max-w-2xl mx-auto space-y-6">
            {Object.entries(grouped).map(([category, categoryPlugins]) => (
              <div key={category}>
                <h2 className="text-sm font-semibold text-base-content/80 mb-2">
                  {CATEGORY_LABELS[category] || category}
                </h2>
                <div className="space-y-2">
                  {categoryPlugins.map((plugin) => (
                    <PluginCard
                      key={plugin.name}
                      plugin={plugin}
                      onClick={() => setSelectedPlugin(plugin.name)}
                    />
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function PluginCard({ plugin, onClick }: { plugin: PluginInfo; onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      className="card bg-base-300 border border-neutral w-full text-left hover:border-primary/30 transition-colors"
    >
      <div className="card-body p-4 flex-row items-center gap-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <p className="text-sm font-medium">{plugin.name}</p>
            <span className="badge badge-xs badge-ghost">v{plugin.version}</span>
            {plugin.is_builtin && (
              <span className="badge badge-xs badge-ghost">built-in</span>
            )}
            {plugin.auto_load && (
              <span className="badge badge-xs badge-accent">auto</span>
            )}
          </div>
          <p className="text-xs text-base-content/60 truncate mt-0.5">
            {plugin.description}
          </p>
        </div>
        <div className="text-xs text-base-content/40">
          {plugin.tools.length} tool{plugin.tools.length !== 1 ? "s" : ""}
        </div>
      </div>
    </button>
  );
}

function groupByCategory(plugins: PluginInfo[]): Record<string, PluginInfo[]> {
  const groups: Record<string, PluginInfo[]> = {};
  for (const plugin of plugins) {
    const cat = plugin.category || "general";
    if (!groups[cat]) groups[cat] = [];
    groups[cat].push(plugin);
  }
  return groups;
}
