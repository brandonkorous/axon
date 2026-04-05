import { useEffect } from "react";
import { useLocation, useParams } from "react-router-dom";
import { useTabStore, type TabType } from "../../stores/tabStore";
import { ROUTE_TO_TAB, TAB_REGISTRY } from "./TabRegistry";
import { useAgents } from "../../hooks/useAgents";

/**
 * Intercepts route navigation and opens the corresponding tab.
 * Renders nothing — the tab content is rendered by TabContent in LayoutShell.
 */
export function TabRedirect() {
  const location = useLocation();
  const params = useParams();
  const { data: agents = [] } = useAgents();

  useEffect(() => {
    const path = location.pathname;
    const openTab = useTabStore.getState().openTab;

    for (const route of ROUTE_TO_TAB) {
      const match = path.match(route.pattern);
      if (!match) continue;

      const extracted = route.extract?.(match) || {};
      const registryEntry = TAB_REGISTRY[route.type];
      let label = extracted.label || registryEntry?.label || route.type;

      // Resolve agent name for chat tabs
      if (route.type === "chat" && extracted.agentId) {
        const agent = agents.find((a) => a.id === extracted.agentId);
        if (agent) label = agent.name;
      }

      openTab({
        type: route.type,
        label,
        agentId: extracted.agentId,
        params: extracted.params,
      });
      return;
    }
  }, [location.pathname, agents]);

  return null;
}
