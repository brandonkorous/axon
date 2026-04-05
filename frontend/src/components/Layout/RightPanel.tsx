import { usePanelStore, type RightPanelView } from "../../stores/panelStore";
import { useTabStore } from "../../stores/tabStore";
import { PluginsSection, SkillsSection, SandboxesSection } from "../AgentControls/ToolbeltSections";
import { CommsSection } from "../AgentControls/CommsSection";
import { ResizeHandle } from "./ResizeHandle";

const VIEW_TITLES: Record<RightPanelView, string> = {
  plugins: "Plugins",
  skills: "Skills",
  sandboxes: "Sandboxes",
  comms: "Communication",
  "agent-config": "Agent Config",
};

const VIEW_TABS: { key: RightPanelView; label: string }[] = [
  { key: "plugins", label: "Plugins" },
  { key: "skills", label: "Skills" },
  { key: "sandboxes", label: "Sandboxes" },
  { key: "comms", label: "Comms" },
];

export function RightPanel() {
  const { rightOpen, rightView, sizes, resizeRight, setRightView, toggleRight } = usePanelStore();
  const activeTabType = useTabStore((s) => {
    const g = s.groups[s.activeGroupId];
    return g?.activeTabId ? s.tabs[g.activeTabId]?.type : undefined;
  });
  const activeTabAgentId = useTabStore((s) => {
    const g = s.groups[s.activeGroupId];
    return g?.activeTabId ? s.tabs[g.activeTabId]?.agentId : undefined;
  });

  if (!rightOpen) return null;

  const agentId = activeTabType === "chat" || activeTabType === "axon"
    ? activeTabAgentId
    : undefined;

  const hasAgentContext = !!agentId;

  return (
    <>
      <ResizeHandle
        direction="horizontal"
        onResize={(delta) => resizeRight(sizes.rightWidth - delta)}
      />
      <aside
        className="bg-base-200 border-l border-base-content/10 flex flex-col overflow-hidden shrink-0"
        style={{ width: sizes.rightWidth }}
      >
        {/* Header with tabs when agent context is available */}
        <div className="border-b border-base-content/10 shrink-0">
          <div className="flex items-center justify-between px-3 py-2">
            <span className="text-xs font-semibold text-base-content/60 uppercase tracking-wider">
              {hasAgentContext ? VIEW_TITLES[rightView] : "Context"}
            </span>
            <button
              onClick={toggleRight}
              className="btn btn-ghost btn-xs btn-square"
              aria-label="Close panel"
            >
              <svg className="w-3.5 h-3.5" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                <path d="M6 6l8 8M14 6l-8 8" />
              </svg>
            </button>
          </div>
          {hasAgentContext && (
            <div className="flex items-center gap-0.5 px-2 pb-1">
              {VIEW_TABS.map((tab) => (
                <button
                  key={tab.key}
                  onClick={() => setRightView(tab.key)}
                  className={`px-2 py-1 text-xs rounded transition-colors ${
                    rightView === tab.key
                      ? "text-base-content bg-base-100 font-medium"
                      : "text-base-content/50 hover:text-base-content"
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-3">
          {hasAgentContext ? (
            <AgentContextContent agentId={agentId!} view={rightView} />
          ) : (
            <NoContextContent activeTabType={activeTabType} />
          )}
        </div>
      </aside>
    </>
  );
}

function AgentContextContent({ agentId, view }: { agentId: string; view: RightPanelView }) {
  switch (view) {
    case "plugins":
      return <PluginsSection agentId={agentId} />;
    case "skills":
      return <SkillsSection agentId={agentId} />;
    case "sandboxes":
      return <SandboxesSection agentId={agentId} />;
    case "comms":
      return <CommsSection agentId={agentId} />;
    default:
      return <p className="text-xs text-base-content/50">No configuration available.</p>;
  }
}

function NoContextContent({ activeTabType }: { activeTabType?: string }) {
  return (
    <div className="text-xs text-base-content/50 space-y-2">
      <p>
        {activeTabType === "tasks" && "Select a task to view details."}
        {activeTabType === "document" && "Document outline and backlinks will appear here."}
        {activeTabType === "memory" && "Memory node details will appear here."}
        {!activeTabType && "Open an agent chat to see plugins, skills, and sandbox configuration."}
        {activeTabType && !["tasks", "document", "memory"].includes(activeTabType) &&
          "Open an agent chat to see plugins, skills, and sandbox configuration."}
      </p>
    </div>
  );
}
