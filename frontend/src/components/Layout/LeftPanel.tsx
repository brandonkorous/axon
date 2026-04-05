import { usePanelStore } from "../../stores/panelStore";
import { useAgents } from "../../hooks/useAgents";
import { usePendingApprovals } from "../../hooks/useApprovals";
import { useTabStore, type TabType } from "../../stores/tabStore";

import { ResizeHandle } from "./ResizeHandle";

const VIEW_TITLES: Record<string, string> = {
  agents: "Agents",
  search: "Search",
  nav: "Navigation",
  extensions: "Extensions",
};

function useOpenTab() {
  const openTab = useTabStore((s) => s.openTab);
  return (type: TabType, label: string, agentId?: string, params?: Record<string, string>) => {
    openTab({ type, label, agentId, params });
  };
}

function NavItem({ type, label, agentId, params, badge, activeTabType, activeAgentId }: {
  type: TabType;
  label: string;
  agentId?: string;
  params?: Record<string, string>;
  badge?: React.ReactNode;
  activeTabType?: TabType;
  activeAgentId?: string;
}) {
  const open = useOpenTab();
  const isActive = activeTabType === type && (!agentId || activeAgentId === agentId);

  return (
    <li>
      <button
        onClick={() => open(type, label, agentId, params)}
        className={isActive ? "menu-active" : ""}
      >
        {badge ? (
          <span className="flex items-center justify-between w-full">
            {label}
            {badge}
          </span>
        ) : label}
      </button>
    </li>
  );
}

function AgentsView() {
  const { data: agents = [] } = useAgents();
  const openTab = useOpenTab();
  const activeTabType = useTabStore((s) => {
    const g = s.groups[s.activeGroupId];
    return g?.activeTabId ? s.tabs[g.activeTabId]?.type : undefined;
  });
  const activeTabAgentId = useTabStore((s) => {
    const g = s.groups[s.activeGroupId];
    return g?.activeTabId ? s.tabs[g.activeTabId]?.agentId : undefined;
  });

  return (
    <div className="flex flex-col gap-1">
      <div className="px-2 py-1">
        <ul className="menu menu-sm w-full gap-0.5">
          {agents.map((agent) => {
            const isActive = activeTabType === "chat" && activeTabAgentId === agent.id;
            return (
              <li key={agent.id}>
                <button
                  onClick={() => openTab("chat", agent.name, agent.id)}
                  className={isActive ? "menu-active" : ""}
                >
                  <span
                    className="w-2 h-2 rounded-full shrink-0"
                    style={{ backgroundColor: agent.ui?.color || "var(--color-primary)" }}
                  />
                  <span className="truncate">{agent.name}</span>
                  {agent.lifecycle?.status === "active" && (
                    <span className="w-1.5 h-1.5 rounded-full bg-success ml-auto shrink-0" />
                  )}
                </button>
              </li>
            );
          })}
        </ul>
      </div>
    </div>
  );
}

function NavigationView() {
  const { data: pendingApprovals } = usePendingApprovals();
  const approvalCount = pendingApprovals?.length ?? 0;
  const activeTabType = useTabStore((s) => {
    const g = s.groups[s.activeGroupId];
    return g?.activeTabId ? s.tabs[g.activeTabId]?.type : undefined;
  });
  const activeTabAgentId = useTabStore((s) => {
    const g = s.groups[s.activeGroupId];
    return g?.activeTabId ? s.tabs[g.activeTabId]?.agentId : undefined;
  });
  const at = activeTabType;
  const aa = activeTabAgentId;

  return (
    <nav className="px-2 py-1" aria-label="Main navigation">
      <ul className="menu menu-sm w-full gap-0.5">
        <NavItem type="axon" label="Axon" activeTabType={at} activeAgentId={aa} />

        <li className="menu-title mt-3">Workspace</li>
        <NavItem type="dashboard" label="Dashboard" activeTabType={at} activeAgentId={aa} />
        <NavItem type="huddle" label="Huddle" activeTabType={at} activeAgentId={aa} />
        <NavItem type="tasks" label="Tasks" activeTabType={at} activeAgentId={aa} />
        <NavItem type="calendar" label="Calendar" activeTabType={at} activeAgentId={aa} />

        <li className="menu-title mt-3">Oversight</li>
        <NavItem
          type="approvals" label="Approvals" activeTabType={at} activeAgentId={aa}
          badge={approvalCount > 0 ? <span className="badge badge-warning badge-xs">{approvalCount}</span> : undefined}
        />
        <NavItem type="issues" label="Issues" activeTabType={at} activeAgentId={aa} />
        <NavItem type="analytics" label="Analytics" activeTabType={at} activeAgentId={aa} />
        <NavItem type="achievements" label="Achievements" activeTabType={at} activeAgentId={aa} />

        <li className="menu-title mt-3">Knowledge</li>
        <NavItem type="documents" label="Documents" activeTabType={at} activeAgentId={aa} />
        <NavItem type="memory" label="Mind" activeTabType={at} activeAgentId={aa} />

        <li className="menu-title mt-3">Admin</li>
        <NavItem type="org-chart" label="Org Chart" activeTabType={at} activeAgentId={aa} />
        <NavItem type="audit" label="Audit Log" activeTabType={at} activeAgentId={aa} />
        <NavItem type="usage" label="Usage" activeTabType={at} activeAgentId={aa} />
      </ul>
    </nav>
  );
}

function SearchView() {
  return (
    <div className="p-3">
      <input
        type="text"
        placeholder="Search conversations, docs, memories..."
        className="input input-sm input-bordered w-full"
        aria-label="Global search"
      />
      <p className="text-xs text-base-content/50 mt-3 px-1">
        Search across all agents, documents, and memories.
      </p>
    </div>
  );
}

function ExtensionsView() {
  const activeTabType = useTabStore((s) => {
    const g = s.groups[s.activeGroupId];
    return g?.activeTabId ? s.tabs[g.activeTabId]?.type : undefined;
  });
  const at = activeTabType;

  return (
    <nav className="px-2 py-1">
      <ul className="menu menu-sm w-full gap-0.5">
        <NavItem type="plugins" label="Plugins" activeTabType={at} />
        <NavItem type="skills" label="Skills" activeTabType={at} />
        <NavItem type="sandboxes" label="Sandboxes" activeTabType={at} />
        <NavItem type="artifacts" label="Artifacts" activeTabType={at} />
      </ul>
    </nav>
  );
}

const VIEWS: Record<string, React.FC> = {
  agents: AgentsView,
  search: SearchView,
  nav: NavigationView,
  extensions: ExtensionsView,
};

export function LeftPanel() {
  const { leftOpen, leftView, sizes, resizeLeft } = usePanelStore();

  if (!leftOpen) return null;

  const ViewComponent = VIEWS[leftView];

  return (
    <>
      <aside
        className="bg-base-200 border-r border-base-content/10 flex flex-col overflow-hidden shrink-0"
        style={{ width: sizes.leftWidth }}
      >
        <div className="px-3 py-2 text-xs font-semibold text-base-content/60 uppercase tracking-wider border-b border-base-content/10">
          {VIEW_TITLES[leftView]}
        </div>
        <div className="flex-1 overflow-y-auto">
          {ViewComponent && <ViewComponent />}
        </div>
      </aside>
      <ResizeHandle
        direction="horizontal"
        onResize={(delta) => resizeLeft(sizes.leftWidth + delta)}
      />
    </>
  );
}
