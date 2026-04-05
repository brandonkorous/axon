import { useEffect, useRef } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { useTabStore } from "../../stores/tabStore";
import { TAB_REGISTRY } from "./TabRegistry";

/**
 * Syncs active tab → URL (one-way).
 * URL → tab is handled by TabRedirect.
 *
 * Subscribes only to activeGroupId to avoid re-fire loops.
 * Reads groups/tabs via getState() to prevent cascading effects.
 */
export function useTabUrlSync() {
  const navigate = useNavigate();
  const location = useLocation();
  const activeGroupId = useTabStore((s) => s.activeGroupId);
  const lastSyncedTabId = useRef<string | null>(null);

  // Subscribe to the active tab id of the active group
  const activeTabId = useTabStore((s) => {
    const group = s.groups[s.activeGroupId];
    return group?.activeTabId ?? null;
  });

  useEffect(() => {
    if (!activeTabId || activeTabId === lastSyncedTabId.current) return;
    lastSyncedTabId.current = activeTabId;

    const { tabs } = useTabStore.getState();
    const tab = tabs[activeTabId];
    if (!tab) return;

    const config = TAB_REGISTRY[tab.type];
    if (!config?.toPath) return;

    const targetPath = config.toPath(tab.agentId, tab.params);
    if (targetPath && targetPath !== location.pathname) {
      navigate(targetPath, { replace: true });
    }
  }, [activeTabId, navigate, location.pathname]);
}
