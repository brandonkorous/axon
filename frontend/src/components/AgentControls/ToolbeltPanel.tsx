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

export function ToolbeltPanel({
  agentId,
  onClose,
}: {
  agentId: string;
  onClose: () => void;
}) {
  return (
    <div className="border-t border-neutral pt-3 space-y-3">
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        <PluginsSection agentId={agentId} />
        <SkillsSection agentId={agentId} />
        <SandboxesSection agentId={agentId} />
      </div>
      <div className="flex justify-end">
        <button onClick={onClose} className="btn btn-ghost btn-xs">
          Close
        </button>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Plugins
// ---------------------------------------------------------------------------

function PluginsSection({ agentId }: { agentId: string }) {
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

function SkillsSection({ agentId }: { agentId: string }) {
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

function SandboxesSection({ agentId }: { agentId: string }) {
  const { images, loading, fetchImages } = useSandboxStore();

  useEffect(() => {
    fetchImages();
  }, [fetchImages]);

  if (loading) return <SectionShell title="Sandboxes" loading />;
  if (images.length === 0) return <SectionShell title="Sandboxes" empty />;

  return (
    <SectionShell title="Sandboxes" subtitle="Execution environments">
      {images.map((img) => (
        <SandboxRow key={img.type} image={img} agentId={agentId} />
      ))}
    </SectionShell>
  );
}

function SandboxRow({
  image,
  agentId,
}: {
  image: SandboxImageInfo;
  agentId: string;
}) {
  const using = image.agents_using?.includes(agentId);
  const badge = SANDBOX_STATUS_BADGE[image.status] || "badge-ghost";

  return (
    <div className="flex items-center justify-between py-1">
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

function SectionShell({
  title,
  subtitle,
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
      <h4 className="text-xs font-semibold text-base-content/70">{title}</h4>
      {subtitle && (
        <p className="text-[11px] text-base-content/40 mb-1.5">{subtitle}</p>
      )}
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
        <div className="space-y-0.5 max-h-48 overflow-y-auto">
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
