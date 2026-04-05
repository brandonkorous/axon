import { useEffect, useState } from "react";
import { NavLink, Outlet, useLocation } from "react-router-dom";
import { SplitContainer } from "./SplitContainer";
import { useTabUrlSync } from "./useTabUrlSync";
import { useOrgStore } from "../../stores/orgStore";
import { useSettingsStore } from "../../stores/settingsStore";
import { useOrgs } from "../../hooks/useOrgs";
import { useAgents } from "../../hooks/useAgents";
import { usePendingApprovals } from "../../hooks/useApprovals";
import { useModelStatus } from "../../hooks/useModels";
import { usePanelStore } from "../../stores/panelStore";
import { useTabStore } from "../../stores/tabStore";
import { StatusBar } from "../StatusBar/StatusBar";
import { VoiceChatOverlay } from "../VoiceChat/VoiceChatOverlay";
import { SettingsModal } from "../Settings/SettingsModal";
import { ModelOnboardingModal } from "../Settings/ModelOnboardingModal";
import { ActivityBar } from "./ActivityBar";
import { LeftPanel } from "./LeftPanel";
import { RightPanel } from "./RightPanel";
import { BottomPanel } from "./BottomPanel";

// Apply stored theme on load
const storedTheme = localStorage.getItem("axon-theme");
if (storedTheme === "axon" || storedTheme === "axon-dark") {
  document.documentElement.setAttribute("data-theme", storedTheme);
} else if (window.matchMedia("(prefers-color-scheme: dark)").matches) {
  document.documentElement.setAttribute("data-theme", "axon-dark");
}

export function LayoutShell() {
  const activeOrgId = useOrgStore((s) => s.activeOrgId);
  const setActiveOrg = useOrgStore((s) => s.setActiveOrg);

  // TanStack Query auto-fetches — no useEffect needed for these
  const { data: orgs } = useOrgs();
  useAgents();
  usePendingApprovals();
  const { data: modelStatus } = useModelStatus();

  // Bridge orgs query data into Zustand store so activeOrgId gets set.
  // The old fetchOrgs() did this internally — TQ queries are data-only.
  useEffect(() => {
    if (!orgs?.length) return;
    const current = activeOrgId;
    const valid = orgs.find((o) => o.id === current);
    if (!valid) {
      setActiveOrg(orgs[0].id);
    }
  }, [orgs, activeOrgId, setActiveOrg]);

  const [showOnboarding, setShowOnboarding] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const location = useLocation();

  // Show onboarding when models are not configured
  useEffect(() => {
    if (modelStatus && !modelStatus.configured) setShowOnboarding(true);
  }, [modelStatus]);

  // Close mobile menu on navigation
  useEffect(() => {
    setMobileMenuOpen(false);
  }, [location.pathname]);

  // Tab ↔ URL sync
  useTabUrlSync();

  // Keyboard shortcuts
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      const ctrl = e.ctrlKey || e.metaKey;
      if (ctrl && e.key === "b") {
        e.preventDefault();
        usePanelStore.getState().toggleLeft();
      }
      if (ctrl && e.key === "j") {
        e.preventDefault();
        usePanelStore.getState().toggleBottom();
      }
      if (ctrl && e.shiftKey && e.key === "B") {
        e.preventDefault();
        usePanelStore.getState().toggleRight();
      }
      // Tab shortcuts
      if (ctrl && e.key === "w") {
        e.preventDefault();
        const s = useTabStore.getState();
        const group = s.groups[s.activeGroupId];
        if (group?.activeTabId) s.closeTab(group.activeTabId);
      }
      if (ctrl && e.key === "Tab") {
        e.preventDefault();
        const s = useTabStore.getState();
        const group = s.groups[s.activeGroupId];
        if (!group || group.tabs.length < 2) return;
        const idx = group.tabs.indexOf(group.activeTabId || "");
        const next = e.shiftKey
          ? (idx - 1 + group.tabs.length) % group.tabs.length
          : (idx + 1) % group.tabs.length;
        s.activateTab(group.tabs[next]);
      }
      // Split shortcuts
      if (ctrl && !e.shiftKey && e.key === "\\") {
        e.preventDefault();
        const s = useTabStore.getState();
        s.splitGroup(s.activeGroupId, "horizontal");
      }
      if (ctrl && e.shiftKey && e.key === "|") {
        e.preventDefault();
        const s = useTabStore.getState();
        s.splitGroup(s.activeGroupId, "vertical");
      }
      // Focus split group by number (Ctrl+1, Ctrl+2, Ctrl+3)
      if (ctrl && !e.shiftKey && e.key >= "1" && e.key <= "9") {
        const s = useTabStore.getState();
        const groupIds = Object.keys(s.groups);
        const idx = parseInt(e.key) - 1;
        if (idx < groupIds.length) {
          e.preventDefault();
          useTabStore.setState({ activeGroupId: groupIds[idx] });
        }
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, []);

  return (
    <div className="flex flex-col h-screen overflow-hidden">
      {/* Main row: activity bar + panels + center + right panel */}
      <div className="flex flex-1 overflow-hidden">
        {/* Activity Bar (desktop only) */}
        <ActivityBar />

        {/* Mobile sidebar */}
        <MobileMenu
          open={mobileMenuOpen}
          onClose={() => setMobileMenuOpen(false)}
        />

        {/* Left Panel (desktop) */}
        <LeftPanel />

        {/* Center area: content + bottom panel */}
        <div className="flex-1 flex flex-col overflow-hidden min-w-0">
          {/* Mobile header */}
          <div className="flex items-center gap-3 px-4 py-2 bg-base-200 border-b border-base-content/10 md:hidden">
            <button
              onClick={() => setMobileMenuOpen(true)}
              className="btn btn-ghost btn-sm btn-square"
              aria-label="Open menu"
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} className="w-5 h-5">
                <path d="M3 12h18M3 6h18M3 18h18" />
              </svg>
            </button>
            <span className="font-[family-name:var(--font-display)] text-base font-bold text-base-content tracking-tight">
              axon
            </span>
          </div>

          {/* Outlet is hidden — TabRedirect intercepts routes and opens tabs */}
          <div className="hidden"><Outlet /></div>

          {/* Split container with tabbed groups */}
          <SplitContainer />

          {/* Bottom Panel */}
          <BottomPanel />
        </div>

        {/* Right Panel */}
        <RightPanel />
      </div>

      {/* Status Bar */}
      <StatusBar />

      {/* Overlays */}
      <VoiceChatOverlay />
      <SettingsModal />
      {showOnboarding && (
        <ModelOnboardingModal onClose={() => setShowOnboarding(false)} />
      )}
    </div>
  );
}

/** Mobile full-screen menu (replaces the old sidebar on mobile) */
function MobileMenu({ open, onClose }: { open: boolean; onClose: () => void }) {
  const openSettings = useSettingsStore((s) => s.open);

  if (!open) return null;

  return (
    <>
      <div className="fixed inset-0 z-40 bg-black/50 md:hidden" onClick={onClose} />
      <div className="fixed inset-y-0 left-0 z-50 w-64 bg-base-200 flex flex-col md:hidden">
        <div className="p-4 flex items-center justify-between">
          <div>
            <h1 className="font-[family-name:var(--font-display)] text-2xl font-bold text-base-content tracking-tight">
              axon
            </h1>
            <p className="text-xs text-base-content/60 mt-1">AI Command Center</p>
          </div>
          <button
            onClick={onClose}
            className="btn btn-ghost btn-sm btn-square"
            aria-label="Close menu"
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} className="w-5 h-5">
              <path d="M18 6L6 18M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="flex-1 overflow-y-auto px-2 py-3">
          {/* On mobile, show the full navigation view inline */}
          <MobileNavContent onClose={onClose} />
        </div>

        <div className="border-t border-base-content/10 p-2">
          <button
            onClick={() => { openSettings(); onClose(); }}
            className="btn btn-ghost btn-sm w-full justify-start"
          >
            Settings
          </button>
        </div>
      </div>
    </>
  );
}

/** Inline navigation for mobile menu */
function MobileNavContent({ onClose }: { onClose: () => void }) {
  const { data: pendingApprovals } = usePendingApprovals();
  const approvalCount = pendingApprovals?.length ?? 0;
  const { data: agents = [] } = useAgents();

  const navClass = ({ isActive }: { isActive: boolean }) => isActive ? "menu-active" : "";

  return (
    <nav aria-label="Mobile navigation">
      <ul className="menu w-full gap-0.5">
        <li><NavLink to="/" onClick={onClose} className={navClass} end>Axon</NavLink></li>
        <li><NavLink to="/dashboard" onClick={onClose} className={navClass}>Dashboard</NavLink></li>

        <li className="menu-title mt-3">Agents</li>
        {agents.map((agent) => (
          <li key={agent.id}>
            <NavLink to={`/agent/${agent.id}`} onClick={onClose} className={navClass}>
              <span className="w-2 h-2 rounded-full shrink-0" style={{ backgroundColor: agent.ui?.color || "var(--color-primary)" }} />
              {agent.name}
            </NavLink>
          </li>
        ))}

        <li className="menu-title mt-3">Workspace</li>
        <li><NavLink to="/huddle" onClick={onClose} className={navClass}>Huddle</NavLink></li>
        <li><NavLink to="/tasks" onClick={onClose} className={navClass}>Tasks</NavLink></li>
        <li><NavLink to="/calendar" onClick={onClose} className={navClass}>Calendar</NavLink></li>

        <li className="menu-title mt-3">Oversight</li>
        <li>
          <NavLink to="/approvals" onClick={onClose} className={navClass}>
            <span className="flex items-center justify-between w-full">
              Approvals
              {approvalCount > 0 && <span className="badge badge-warning badge-xs">{approvalCount}</span>}
            </span>
          </NavLink>
        </li>
        <li><NavLink to="/issues" onClick={onClose} className={navClass}>Issues</NavLink></li>
        <li><NavLink to="/analytics" onClick={onClose} className={navClass}>Analytics</NavLink></li>

        <li className="menu-title mt-3">Knowledge</li>
        <li><NavLink to="/documents" onClick={onClose} className={navClass}>Documents</NavLink></li>
        <li><NavLink to="/mind" onClick={onClose} className={navClass}>Mind</NavLink></li>

        <li className="menu-title mt-3">Extensions</li>
        <li><NavLink to="/plugins" onClick={onClose} className={navClass}>Plugins</NavLink></li>
        <li><NavLink to="/skills" onClick={onClose} className={navClass}>Skills</NavLink></li>
        <li><NavLink to="/sandboxes" onClick={onClose} className={navClass}>Sandboxes</NavLink></li>
      </ul>
    </nav>
  );
}
