import { useToolbeltSidebarStore, SidebarTab } from "../../stores/toolbeltSidebarStore";
import { PluginsSection, SkillsSection, SandboxesSection } from "./ToolbeltSections";
import { CommsSection } from "./CommsSection";

const TAB_META: Record<SidebarTab, { label: string; description: string }> = {
  plugins: { label: "Plugins", description: "Tool-providing modules" },
  skills: { label: "Skills", description: "Reasoning patterns" },
  sandboxes: { label: "Sandboxes", description: "Execution environments" },
  comms: { label: "Communication", description: "Email, messaging & action style" },
};

export function SidebarPanel({ agentId }: { agentId: string }) {
  const { activeTab, close } = useToolbeltSidebarStore();

  return (
    <div className="flex flex-col h-full min-w-80">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-neutral shrink-0">
        <div>
          <h3 className="text-xs font-semibold text-base-content/70 uppercase tracking-wide">
            {TAB_META[activeTab].label}
          </h3>
          <p className="text-[11px] text-base-content/40">
            {TAB_META[activeTab].description}
          </p>
        </div>
        <button
          onClick={close}
          className="btn btn-ghost btn-xs btn-square"
          aria-label="Close panel"
        >
          <svg className="w-3.5 h-3.5" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
            <path d="M4 4l8 8M12 4l-8 8" />
          </svg>
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4">
        {activeTab === "plugins" && <PluginsSection agentId={agentId} />}
        {activeTab === "skills" && <SkillsSection agentId={agentId} />}
        {activeTab === "sandboxes" && <SandboxesSection agentId={agentId} />}
        {activeTab === "comms" && <CommsSection agentId={agentId} />}
      </div>
    </div>
  );
}
