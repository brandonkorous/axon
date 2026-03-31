import { useEffect, useState } from "react";
import { NavLink, Outlet, useLocation } from "react-router-dom";
import { useOrgStore } from "../stores/orgStore";
import { OrgSwitcher } from "./OrgSwitcher";
import { VoiceChatOverlay } from "./VoiceChat/VoiceChatOverlay";
import { SettingsModal } from "./Settings/SettingsModal";
import { ModelOnboardingModal } from "./Settings/ModelOnboardingModal";
import { useSettingsStore } from "../stores/settingsStore";
import { useApprovalStore } from "../stores/approvalStore";
import { useAgentStore } from "../stores/agentStore";
import { useModelStore } from "../stores/modelStore";
import { StatusBar } from "./StatusBar/StatusBar";

// Apply stored theme on load (GeneralTab manages it when settings are open)
const storedTheme = localStorage.getItem("axon-theme");
if (storedTheme === "axon" || storedTheme === "axon-dark") {
  document.documentElement.setAttribute("data-theme", storedTheme);
} else if (window.matchMedia("(prefers-color-scheme: dark)").matches) {
  document.documentElement.setAttribute("data-theme", "axon-dark");
}

export function Layout() {
  const fetchAgents = useAgentStore((s) => s.fetchAgents);
  const { fetchOrgs, activeOrgId } = useOrgStore();
  const openSettings = useSettingsStore((s) => s.open);
  const approvalCount = useApprovalStore((s) => s.approvals.length);
  const fetchPending = useApprovalStore((s) => s.fetchPending);
  const modelStatus = useModelStore((s) => s.status);
  const fetchModelStatus = useModelStore((s) => s.fetchStatus);
  const [showOnboarding, setShowOnboarding] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const location = useLocation();

  useEffect(() => {
    fetchOrgs().then(() => fetchAgents());
  }, [fetchOrgs, fetchAgents]);

  useEffect(() => {
    if (activeOrgId) fetchModelStatus();
  }, [activeOrgId, fetchModelStatus]);

  useEffect(() => {
    if (modelStatus && !modelStatus.configured) setShowOnboarding(true);
  }, [modelStatus]);

  useEffect(() => {
    fetchPending();
    const interval = setInterval(fetchPending, 30_000);
    return () => clearInterval(interval);
  }, [fetchPending]);


  // Close sidebar on navigation (mobile)
  useEffect(() => {
    setSidebarOpen(false);
  }, [location.pathname]);

  return (
    <div className="flex flex-col h-screen">
      <div className="flex flex-1 overflow-hidden">
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

            <li className="menu-title mt-4">Workspace</li>
            <li>
              <NavLink to="/dashboard" className={({ isActive }) => isActive ? "menu-active" : ""}>
                Dashboard
              </NavLink>
            </li>
            <li>
              <NavLink to="/huddle" className={({ isActive }) => isActive ? "menu-active" : ""}>
                Huddle
              </NavLink>
            </li>
            <li>
              <NavLink to="/tasks" className={({ isActive }) => isActive ? "menu-active" : ""}>
                Tasks
              </NavLink>
            </li>
            <li>
              <NavLink to="/calendar" className={({ isActive }) => isActive ? "menu-active" : ""}>
                Calendar
              </NavLink>
            </li>

            <li className="menu-title mt-4">Oversight</li>
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
              <NavLink to="/analytics" className={({ isActive }) => isActive ? "menu-active" : ""}>
                Analytics
              </NavLink>
            </li>
            <li>
              <NavLink to="/achievements" className={({ isActive }) => isActive ? "menu-active" : ""}>
                Achievements
              </NavLink>
            </li>

            <li className="menu-title mt-4">Knowledge</li>
            <li>
              <NavLink to="/mind" className={({ isActive }) => isActive ? "menu-active" : ""}>
                Mind
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
              <NavLink to="/sandboxes" className={({ isActive }) => isActive ? "menu-active" : ""}>
                Sandboxes
              </NavLink>
            </li>
            <li>
              <NavLink to="/artifacts" className={({ isActive }) => isActive ? "menu-active" : ""}>
                Artifacts
              </NavLink>
            </li>

            <li className="menu-title mt-4">Admin</li>
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
      </div>

      <StatusBar />

      <VoiceChatOverlay />
      <SettingsModal />
      {showOnboarding && (
        <ModelOnboardingModal onClose={() => setShowOnboarding(false)} />
      )}
    </div>
  );
}
