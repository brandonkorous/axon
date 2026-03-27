import { useEffect, useState } from "react";
import { NavLink, Outlet, useLocation } from "react-router-dom";
import { useAgentStore } from "../stores/agentStore";
import { useThinkingAgents } from "../stores/agentRuntimeStore";
import { useOrgStore } from "../stores/orgStore";
import { StatusBadge } from "./AgentControls/AgentControls";
import { OrgSwitcher } from "./OrgSwitcher";
import { VoiceChatFAB } from "./VoiceChat/VoiceChatFAB";
import { VoiceChatOverlay } from "./VoiceChat/VoiceChatOverlay";
import { SettingsModal } from "./Settings/SettingsModal";
import { useSettingsStore } from "../stores/settingsStore";
import { useApprovalStore } from "../stores/approvalStore";
import { useInboxStore } from "../stores/inboxStore";

// Apply stored theme on load (GeneralTab manages it when settings are open)
const storedTheme = localStorage.getItem("axon-theme");
if (storedTheme === "axon" || storedTheme === "axon-dark") {
  document.documentElement.setAttribute("data-theme", storedTheme);
} else if (window.matchMedia("(prefers-color-scheme: dark)").matches) {
  document.documentElement.setAttribute("data-theme", "axon-dark");
}

export function Layout() {
  const { agents, fetchAgents, loading } = useAgentStore();
  const thinkingAgentIds = useThinkingAgents();
  const { fetchOrgs } = useOrgStore();
  const openSettings = useSettingsStore((s) => s.open);
  const approvalCount = useApprovalStore((s) => s.approvals.length);
  const fetchPending = useApprovalStore((s) => s.fetchPending);
  const inboxPendingCount = useInboxStore(
    (s) => s.items.filter((i) => i.status === "pending").length
  );
  const fetchInbox = useInboxStore((s) => s.fetchAll);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const location = useLocation();

  useEffect(() => {
    fetchOrgs().then(() => fetchAgents());
  }, [fetchOrgs, fetchAgents]);

  useEffect(() => {
    fetchPending();
    const interval = setInterval(fetchPending, 30_000);
    return () => clearInterval(interval);
  }, [fetchPending]);

  useEffect(() => {
    fetchInbox();
    const interval = setInterval(fetchInbox, 60_000);
    return () => clearInterval(interval);
  }, [fetchInbox]);

  // Close sidebar on navigation (mobile)
  useEffect(() => {
    setSidebarOpen(false);
  }, [location.pathname]);

  return (
    <div className="flex h-screen">
      {/* Mobile backdrop */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-30 bg-black/50 md:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      <aside className={`fixed z-40 inset-y-0 left-0 w-64 bg-base-200 flex flex-col transition-transform duration-200 md:static md:translate-x-0 ${sidebarOpen ? "translate-x-0" : "-translate-x-full"}`}>
        <div className="p-4 flex items-center justify-between">
          <div>
            <h1 className="font-[family-name:var(--font-display)] text-2xl font-bold text-base-content tracking-tight">
              axon
            </h1>
            <p className="text-xs text-base-content/60 mt-1">AI Command Center</p>
          </div>
          <button
            onClick={() => setSidebarOpen(false)}
            className="btn btn-ghost btn-sm btn-square md:hidden"
            aria-label="Close sidebar"
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} className="w-5 h-5"><path d="M18 6L6 18M6 6l12 12" /></svg>
          </button>
        </div>

        <OrgSwitcher />

        <nav className="flex-1 px-2 py-3 overflow-y-auto" aria-label="Main navigation">
          <ul className="menu w-full gap-0.5">
            <li>
              <NavLink to="/" className={({ isActive }) => isActive ? "menu-active" : ""} end>
                Axon
              </NavLink>
            </li>
            <li>
              <NavLink to="/huddle" className={({ isActive }) => isActive ? "menu-active" : ""}>
                Huddle
              </NavLink>
            </li>
            <li>
              <NavLink to="/dashboard" className={({ isActive }) => isActive ? "menu-active" : ""}>
                Dashboard
              </NavLink>
            </li>
            <li>
              <NavLink to="/inbox" className={({ isActive }) => isActive ? "menu-active" : ""}>
                <span className="flex items-center justify-between w-full">
                  Inbox
                  {inboxPendingCount > 0 && (
                    <span className="badge badge-info badge-xs">{inboxPendingCount}</span>
                  )}
                </span>
              </NavLink>
            </li>
            <li>
              <NavLink to="/tasks" className={({ isActive }) => isActive ? "menu-active" : ""}>
                Tasks
              </NavLink>
            </li>
            <li>
              <NavLink to="/approvals" className={({ isActive }) => isActive ? "menu-active" : ""}>
                <span className="flex items-center justify-between w-full">
                  Approvals
                  {approvalCount > 0 && (
                    <span className="badge badge-warning badge-xs">{approvalCount}</span>
                  )}
                </span>
              </NavLink>
            </li>
            <li>
              <NavLink to="/issues" className={({ isActive }) => isActive ? "menu-active" : ""}>
                Issues
              </NavLink>
            </li>
            <li>
              <NavLink to="/achievements" className={({ isActive }) => isActive ? "menu-active" : ""}>
                Achievements
              </NavLink>
            </li>
            <li>
              <NavLink to="/org-chart" className={({ isActive }) => isActive ? "menu-active" : ""}>
                Org Chart
              </NavLink>
            </li>
            <li>
              <NavLink to="/audit" className={({ isActive }) => isActive ? "menu-active" : ""}>
                Audit Log
              </NavLink>
            </li>
            <li>
              <NavLink to="/usage" className={({ isActive }) => isActive ? "menu-active" : ""}>
                Usage
              </NavLink>
            </li>

            <li className="menu-title mt-4">Agents</li>
            {!loading &&
              agents
                .filter((a) => a.id !== "axon" && a.type !== "external" && !a.parent_id)
                .map((agent) => {
                  const children = agents.filter((a) => a.parent_id === agent.id);
                  return (
                    <li key={agent.id}>
                      <NavLink
                        to={`/agent/${agent.id}`}
                        className={({ isActive }) => isActive ? "menu-active" : ""}
                      >
                        <span className="flex items-center gap-2">
                          <span
                            className={`w-2 h-2 rounded-full${thinkingAgentIds.includes(agent.id) ? " animate-pulse" : ""}`}
                            style={{ backgroundColor: agent.ui.color }}
                          />
                          {agent.name}
                          {agent.lifecycle && agent.lifecycle.status !== "active" && (
                            <StatusBadge status={agent.lifecycle.status} />
                          )}
                        </span>
                      </NavLink>
                      {children.length > 0 && (
                        <ul className="ml-2 border-l border-base-content/10">
                          {children.map((child) => (
                            <li key={child.id}>
                              <NavLink
                                to={`/agent/${child.id}`}
                                className={({ isActive }) => isActive ? "menu-active" : ""}
                              >
                                <span className="flex items-center gap-2">
                                  <span
                                    className={`w-1.5 h-1.5 rounded-full${thinkingAgentIds.includes(child.id) ? " animate-pulse" : ""}`}
                                    style={{ backgroundColor: child.ui.color }}
                                  />
                                  <span className="text-xs">{child.name}</span>
                                  {child.lifecycle && child.lifecycle.status !== "active" && (
                                    <StatusBadge status={child.lifecycle.status} />
                                  )}
                                </span>
                              </NavLink>
                            </li>
                          ))}
                        </ul>
                      )}
                    </li>
                  );
                })}

            <li className="menu-title mt-4">Workers</li>
            <li>
              <NavLink to="/workers" className={({ isActive }) => isActive ? "menu-active" : ""} end>
                All Workers
              </NavLink>
            </li>
            <li>
              <NavLink to="/workers/new" className={({ isActive }) => isActive ? "menu-active" : ""}>
                + Add Worker
              </NavLink>
            </li>

            <li className="menu-title mt-4">Extensions</li>
            <li>
              <NavLink to="/plugins" className={({ isActive }) => isActive ? "menu-active" : ""}>
                Plugins
              </NavLink>
            </li>
            <li>
              <NavLink to="/skills" className={({ isActive }) => isActive ? "menu-active" : ""}>
                Skills
              </NavLink>
            </li>
            <li>
              <NavLink to="/artifacts" className={({ isActive }) => isActive ? "menu-active" : ""}>
                Artifacts
              </NavLink>
            </li>

            <li className="menu-title mt-4">Knowledge</li>
            <li>
              <NavLink to="/mind" className={({ isActive }) => isActive ? "menu-active" : ""}>
                Mind
              </NavLink>
            </li>

            <li className="menu-title mt-4">Settings</li>
            <li>
              <button onClick={() => openSettings()}>
                Settings
              </button>
            </li>
          </ul>
        </nav>

      </aside>

      <main className="flex-1 overflow-hidden flex flex-col">
        {/* Mobile header */}
        <div className="flex items-center gap-3 px-4 py-3 bg-base-200 md:hidden">
          <button
            onClick={() => setSidebarOpen(true)}
            className="btn btn-ghost btn-sm btn-square"
            aria-label="Open sidebar"
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} className="w-5 h-5"><path d="M3 12h18M3 6h18M3 18h18" /></svg>
          </button>
          <span className="font-[family-name:var(--font-display)] text-base font-bold text-base-content tracking-tight">axon</span>
        </div>
        <div className="flex-1 overflow-hidden">
          <Outlet />
        </div>
      </main>

      <VoiceChatFAB />
      <VoiceChatOverlay />
      <SettingsModal />
    </div>
  );
}
