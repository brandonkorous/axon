import { useEffect, useState } from "react";
import { usePluginStore, PluginInfo } from "../../stores/pluginStore";
import { useSkillStore, SkillInfo } from "../../stores/skillStore";
import { useSandboxStore, SandboxImageInfo } from "../../stores/sandboxStore";
import { orgApiPath } from "../../stores/orgStore";

const SANDBOX_STATUS_BADGE: Record<string, string> = {
  ready: "badge-success",
  building: "badge-warning",
  error: "badge-error",
  idle: "badge-ghost",
};

// ---------------------------------------------------------------------------
// Plugins
// ---------------------------------------------------------------------------

export function PluginsSection({ agentId }: { agentId: string }) {
  const { plugins, loading, fetchPlugins, enablePlugin, disablePlugin } =
    usePluginStore();
  const [enabledMap, setEnabledMap] = useState<Record<string, boolean>>({});
  const [toggling, setToggling] = useState<string | null>(null);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    fetchPlugins();
  }, [fetchPlugins]);

  useEffect(() => {
    if (plugins.length === 0) return;
    loadEnabledState(plugins.map((p) => p.name), "plugins", agentId).then(
      (m) => {
        setEnabledMap(m);
        setLoaded(true);
      },
    );
  }, [plugins, agentId]);

  const handleToggle = async (plugin: PluginInfo) => {
    const enabled = enabledMap[plugin.name] ?? false;
    setToggling(plugin.name);
    if (enabled) {
      await disablePlugin(plugin.name, agentId);
    } else {
      await enablePlugin(plugin.name, agentId);
    }
    setEnabledMap((prev) => ({ ...prev, [plugin.name]: !enabled }));
    setToggling(null);
  };

  if (loading || (!loaded && plugins.length > 0)) {
    return <SectionShell title="Plugins" loading />;
  }
  if (plugins.length === 0) {
    return <SectionShell title="Plugins" empty />;
  }

  return (
    <SectionShell title="Plugins" subtitle="Tool-providing modules">
      {plugins.map((p) => (
        <ToggleRow
          key={p.name}
          label={p.name}
          description={p.description}
          icon={p.icon}
          enabled={enabledMap[p.name] ?? false}
          toggling={toggling === p.name}
          onToggle={() => handleToggle(p)}
          badge={p.is_builtin ? "built-in" : undefined}
        />
      ))}
    </SectionShell>
  );
}

// ---------------------------------------------------------------------------
// Skills
// ---------------------------------------------------------------------------

export function SkillsSection({ agentId }: { agentId: string }) {
  const { skills, loading, fetchSkills, enableSkill, disableSkill } =
    useSkillStore();
  const [enabledMap, setEnabledMap] = useState<Record<string, boolean>>({});
  const [toggling, setToggling] = useState<string | null>(null);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    fetchSkills();
  }, [fetchSkills]);

  useEffect(() => {
    if (skills.length === 0) return;
    loadEnabledState(skills.map((s) => s.name), "skills", agentId).then(
      (m) => {
        setEnabledMap(m);
        setLoaded(true);
      },
    );
  }, [skills, agentId]);

  const handleToggle = async (skill: SkillInfo) => {
    const enabled = enabledMap[skill.name] ?? false;
    setToggling(skill.name);
    if (enabled) {
      await disableSkill(skill.name, agentId);
    } else {
      await enableSkill(skill.name, agentId);
    }
    setEnabledMap((prev) => ({ ...prev, [skill.name]: !enabled }));
    setToggling(null);
  };

  if (loading || (!loaded && skills.length > 0)) {
    return <SectionShell title="Skills" loading />;
  }
  if (skills.length === 0) {
    return <SectionShell title="Skills" empty />;
  }

  return (
    <SectionShell title="Skills" subtitle="Reasoning patterns">
      {skills.map((s) => (
        <ToggleRow
          key={s.name}
          label={s.name}
          description={s.description}
          icon={s.icon}
          enabled={enabledMap[s.name] ?? false}
          toggling={toggling === s.name}
          onToggle={() => handleToggle(s)}
          badge={s.is_builtin ? "built-in" : undefined}
        />
      ))}
    </SectionShell>
  );
}

// ---------------------------------------------------------------------------
// Sandboxes
// ---------------------------------------------------------------------------

export function SandboxesSection({ agentId }: { agentId: string }) {
  const { images, loading, fetchImages, buildImage, removeImage,
    subscribeBuildProgress, unsubscribeBuildProgress, buildProgress } = useSandboxStore();

  useEffect(() => {
    fetchImages();
  }, [fetchImages]);

  if (loading) return <SectionShell title="Sandboxes" loading />;
  if (images.length === 0) return <SectionShell title="Sandboxes" empty />;

  return (
    <SectionShell title="Sandboxes" subtitle="Execution environments">
      {images.map((img) => (
        <SandboxRow
          key={img.type}
          image={img}
          agentId={agentId}
          progress={buildProgress[img.type]}
          onBuild={async () => {
            const ok = await buildImage(img.type);
            if (ok) subscribeBuildProgress(img.type, () => {
              unsubscribeBuildProgress(img.type);
              fetchImages();
            });
          }}
          onRemove={() => removeImage(img.type)}
        />
      ))}
    </SectionShell>
  );
}

function SandboxRow({
  image,
  agentId,
  progress,
  onBuild,
  onRemove,
}: {
  image: SandboxImageInfo;
  agentId: string;
  progress?: string[];
  onBuild: () => void;
  onRemove: () => void;
}) {
  const using = image.agents_using?.includes(agentId);
  const badge = SANDBOX_STATUS_BADGE[image.status] || "badge-ghost";
  const isBuilding = image.status === "building";
  const isReady = image.status === "ready";
  const isIdle = image.status === "idle";
  const isError = image.status === "error";

  return (
    <div className="py-2 border-b border-neutral/30 last:border-b-0">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 min-w-0">
          <span className="text-xs font-medium truncate">{image.type}</span>
          <span className={`badge badge-xs ${badge}`}>{image.status}</span>
          {using && (
            <span className="badge badge-xs badge-primary badge-outline">
              assigned
            </span>
          )}
        </div>
        {image.size_mb != null && (
          <span className="text-[11px] text-base-content/50 shrink-0">
            {image.size_mb} MB
          </span>
        )}
      </div>
      {image.description && (
        <p className="text-[11px] text-base-content/50 mt-0.5">{image.description}</p>
      )}
      <div className="flex items-center gap-1.5 mt-1.5">
        {(isIdle || isError) && (
          <button onClick={onBuild} className="btn btn-soft btn-primary btn-xs">
            Build
          </button>
        )}
        {isReady && (
          <button onClick={onRemove} className="btn btn-soft btn-error btn-xs">
            Remove
          </button>
        )}
        {isBuilding && (
          <span className="flex items-center gap-1.5 text-[11px] text-warning">
            <span className="loading loading-spinner loading-xs" />
            Building...
          </span>
        )}
      </div>
      {isBuilding && progress && progress.length > 0 && (
        <div className="mt-1.5 bg-base-300 rounded p-2 max-h-24 overflow-y-auto font-mono text-[10px] text-base-content/60">
          {progress.slice(-8).map((line, i) => (
            <div key={i}>{line}</div>
          ))}
        </div>
      )}
      {isError && image.error && (
        <p className="text-[11px] text-error mt-1">{image.error}</p>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Shared helpers
// ---------------------------------------------------------------------------

async function loadEnabledState(
  names: string[],
  resource: "plugins" | "skills",
  agentId: string,
): Promise<Record<string, boolean>> {
  const map: Record<string, boolean> = {};
  await Promise.all(
    names.map(async (name) => {
      try {
        const res = await fetch(orgApiPath(`${resource}/${name}`));
        if (res.ok) {
          const data = await res.json();
          map[name] = (data.agents_using as string[] || []).includes(agentId);
        }
      } catch {
        /* skip */
      }
    }),
  );
  return map;
}

export function SectionShell({
  title,
  loading,
  empty,
  children,
}: {
  title: string;
  subtitle?: string;
  loading?: boolean;
  empty?: boolean;
  children?: React.ReactNode;
}) {
  return (
    <div>
      {loading && (
        <div className="flex items-center gap-2 py-1">
          <span className="loading loading-spinner loading-xs" />
          <span className="text-[11px] text-base-content/50">Loading...</span>
        </div>
      )}
      {empty && (
        <p className="text-[11px] text-base-content/50">
          No {title.toLowerCase()} available.
        </p>
      )}
      {children && (
        <div className="space-y-0.5">
          {children}
        </div>
      )}
    </div>
  );
}

function ToggleRow({
  label,
  description,
  icon,
  enabled,
  toggling,
  onToggle,
  badge,
}: {
  label: string;
  description: string;
  icon: string;
  enabled: boolean;
  toggling: boolean;
  onToggle: () => void;
  badge?: string;
}) {
  return (
    <label className="flex items-center justify-between py-1 cursor-pointer group">
      <div className="flex items-center gap-2 min-w-0">
        {icon && <span className="text-sm shrink-0">{icon}</span>}
        <div className="min-w-0">
          <span className="text-xs font-medium flex items-center gap-1.5">
            {label}
            {badge && (
              <span className="badge badge-xs badge-ghost">{badge}</span>
            )}
          </span>
          <p className="text-[11px] text-base-content/50 truncate">
            {description}
          </p>
        </div>
      </div>
      {toggling ? (
        <span className="loading loading-spinner loading-xs shrink-0" />
      ) : (
        <input
          type="checkbox"
          className="toggle toggle-xs toggle-primary shrink-0"
          checked={enabled}
          onChange={onToggle}
        />
      )}
    </label>
  );
}
