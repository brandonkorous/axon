import { useRef, useCallback, useMemo } from "react";
import { useTabStore, type Tab } from "../../stores/tabStore";

interface TabBarProps {
  groupId: string;
}

export function TabBar({ groupId }: TabBarProps) {
  // Stable selectors — primitives and identity-stable references
  const tabIds = useTabStore((s) => s.groups[groupId]?.tabs) ?? [];
  const activeTabId = useTabStore((s) => s.groups[groupId]?.activeTabId) ?? null;
  const isActiveGroup = useTabStore((s) => s.activeGroupId === groupId);
  const allTabs = useTabStore((s) => s.tabs);

  const tabs = useMemo(() => tabIds.map((id) => allTabs[id]).filter(Boolean), [tabIds, allTabs]);

  const dragTabId = useRef<string | null>(null);
  const dragOverIdx = useRef<number | null>(null);

  const handleDragStart = useCallback((e: React.DragEvent, tabId: string) => {
    dragTabId.current = tabId;
    e.dataTransfer.effectAllowed = "move";
    e.dataTransfer.setData("text/axon-tab", tabId);
    useTabStore.getState().setTabDragging(true);
    const cleanup = () => {
      useTabStore.getState().setTabDragging(false);
      document.removeEventListener("dragend", cleanup);
      document.removeEventListener("drop", cleanup);
    };
    document.addEventListener("dragend", cleanup);
    document.addEventListener("drop", cleanup);
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent, idx: number) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = "move";
    dragOverIdx.current = idx;
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    const tabId = e.dataTransfer.getData("text/axon-tab");
    if (tabId && dragOverIdx.current !== null) {
      useTabStore.getState().moveTab(tabId, dragOverIdx.current, groupId);
    }
    dragTabId.current = null;
    dragOverIdx.current = null;
  }, [groupId]);

  const handleMouseDown = useCallback((e: React.MouseEvent, tabId: string) => {
    if (e.button === 1) {
      e.preventDefault();
      useTabStore.getState().closeTab(tabId);
    }
  }, []);

  if (tabs.length === 0) return null;

  return (
    <div
      className={`flex items-end bg-base-200 border-b h-9 shrink-0 overflow-x-auto select-none ${
        isActiveGroup ? "border-base-content/10" : "border-base-content/5"
      }`}
      onDragOver={(e) => { e.preventDefault(); e.dataTransfer.dropEffect = "move"; }}
      onDrop={handleDrop}
    >
      {tabs.map((tab, idx) => (
        <TabItem
          key={tab.id}
          tab={tab}
          isActive={tab.id === activeTabId}
          isGroupActive={isActiveGroup}
          onActivate={() => useTabStore.getState().activateTab(tab.id)}
          onClose={() => useTabStore.getState().closeTab(tab.id)}
          onMouseDown={(e) => handleMouseDown(e, tab.id)}
          onDragStart={(e) => handleDragStart(e, tab.id)}
          onDragOver={(e) => handleDragOver(e, idx)}
        />
      ))}
    </div>
  );
}

interface TabItemProps {
  tab: Tab;
  isActive: boolean;
  isGroupActive: boolean;
  onActivate: () => void;
  onClose: () => void;
  onMouseDown: (e: React.MouseEvent) => void;
  onDragStart: (e: React.DragEvent) => void;
  onDragOver: (e: React.DragEvent) => void;
}

function TabItem({ tab, isActive, isGroupActive, onActivate, onClose, onMouseDown, onDragStart, onDragOver }: TabItemProps) {
  return (
    <div
      className={`group flex items-center gap-1.5 h-full px-3 text-xs cursor-pointer border-r border-base-content/5 transition-colors ${
        isActive
          ? isGroupActive
            ? "bg-base-100 text-base-content border-b-2 border-b-primary"
            : "bg-base-100/70 text-base-content/80 border-b-2 border-b-base-content/20"
          : "text-base-content/60 hover:text-base-content hover:bg-base-100/50"
      } ${tab.pinned ? "max-w-[40px]" : "max-w-[180px]"}`}
      onClick={onActivate}
      onMouseDown={onMouseDown}
      draggable
      onDragStart={onDragStart}
      onDragOver={onDragOver}
      title={tab.label}
      role="tab"
      aria-selected={isActive}
    >
      {!tab.pinned && <span className="truncate">{tab.label}</span>}
      {tab.pinned && <span className="truncate text-[10px]">{tab.label.charAt(0).toUpperCase()}</span>}
      {!tab.pinned && (
        <button
          onClick={(e) => { e.stopPropagation(); onClose(); }}
          className="w-4 h-4 rounded flex items-center justify-center shrink-0 opacity-0 group-hover:opacity-100 hover:bg-base-content/10 transition-opacity"
          aria-label={`Close ${tab.label}`}
        >
          <svg className="w-3 h-3" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
            <path d="M4 4l8 8M12 4l-8 8" />
          </svg>
        </button>
      )}
    </div>
  );
}
