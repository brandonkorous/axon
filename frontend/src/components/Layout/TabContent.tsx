import { Suspense, useMemo } from "react";
import { useTabStore, type TabType } from "../../stores/tabStore";
import { TAB_REGISTRY } from "./TabRegistry";

interface TabContentProps {
  groupId: string;
}

/** Extract stable primitives from the active tab in one selector */
function useActiveTabInfo(groupId: string) {
  return useTabStore((s) => {
    const group = s.groups[groupId];
    if (!group?.activeTabId) return null;
    const tab = s.tabs[group.activeTabId];
    if (!tab) return null;
    // Return a string key that only changes when the relevant data changes
    return `${tab.id}\0${tab.type}\0${tab.agentId || ""}\0${JSON.stringify(tab.params || {})}`;
  });
}

function parseTabInfo(key: string | null) {
  if (!key) return null;
  const [id, type, agentId, paramsJson] = key.split("\0");
  return {
    id,
    type: type as TabType,
    agentId: agentId || undefined,
    params: JSON.parse(paramsJson) as Record<string, string> | undefined,
  };
}

export function TabContent({ groupId }: TabContentProps) {
  const tabKey = useActiveTabInfo(groupId);
  const info = useMemo(() => parseTabInfo(tabKey), [tabKey]);

  if (!info) {
    return <EmptyState />;
  }

  const config = TAB_REGISTRY[info.type];
  if (!config) {
    return <EmptyState />;
  }

  return (
    <div className="flex-1 overflow-hidden h-full">
      <Suspense fallback={<LoadingFallback />}>
        <TabRenderer
          tabId={info.id}
          agentId={info.agentId}
          params={info.params}
          Component={config.component}
        />
      </Suspense>
    </div>
  );
}

function TabRenderer({ tabId, agentId, params, Component }: {
  tabId: string;
  agentId?: string;
  params?: Record<string, string>;
  Component: React.ComponentType<any>;
}) {
  const element = useMemo(() => {
    return <Component agentId={agentId} {...(params || {})} />;
  }, [tabId, agentId, Component]);

  return element;
}

function EmptyState() {
  return (
    <div className="flex items-center justify-center h-full text-base-content/30">
      <div className="text-center">
        <h2 className="font-[family-name:var(--font-display)] text-2xl font-bold mb-2">axon</h2>
        <p className="text-sm">Open an agent or view from the sidebar to get started.</p>
        <p className="text-xs mt-2 text-base-content/20">Ctrl+B to toggle the sidebar</p>
      </div>
    </div>
  );
}

function LoadingFallback() {
  return (
    <div className="flex items-center justify-center h-full">
      <span className="loading loading-spinner loading-sm text-primary" />
    </div>
  );
}
