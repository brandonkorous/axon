import { create } from "zustand";

export type TabType =
  | "chat"
  | "axon"
  | "dashboard"
  | "huddle"
  | "document"
  | "documents"
  | "memory"
  | "tasks"
  | "calendar"
  | "analytics"
  | "achievements"
  | "approvals"
  | "issues"
  | "org-chart"
  | "audit"
  | "usage"
  | "plugins"
  | "plugin-create"
  | "skills"
  | "skill-create"
  | "sandboxes"
  | "artifacts"
  | "repos"
  | "welcome";

export interface Tab {
  id: string;
  type: TabType;
  label: string;
  agentId?: string;
  params?: Record<string, string>;
  pinned?: boolean;
  groupId: string;
}

export interface TabGroup {
  id: string;
  tabs: string[];       // tab ids in order
  activeTabId: string | null;
}

export type SplitDirection = "horizontal" | "vertical";

export type SplitNode =
  | { type: "leaf"; groupId: string }
  | { type: "branch"; direction: SplitDirection; children: SplitNode[]; sizes: number[] };

interface TabStore {
  tabs: Record<string, Tab>;
  groups: Record<string, TabGroup>;
  splitRoot: SplitNode;
  activeGroupId: string;
  tabDragging: boolean;
  setTabDragging: (v: boolean) => void;

  // Tab operations
  openTab: (tab: Omit<Tab, "id" | "groupId">, groupId?: string) => string;
  closeTab: (tabId: string) => void;
  closeOtherTabs: (tabId: string) => void;
  closeAllTabs: () => void;
  activateTab: (tabId: string) => void;
  moveTab: (tabId: string, toIndex: number, targetGroupId?: string) => void;
  pinTab: (tabId: string) => void;
  unpinTab: (tabId: string) => void;
  updateTabLabel: (tabId: string, label: string) => void;

  // Split operations
  splitGroup: (groupId: string, direction: SplitDirection, tabId?: string) => string;
  resizeSplit: (path: number[], sizes: number[]) => void;

  // Convenience
  openAgentChat: (agentId: string, agentName: string) => void;
  findTab: (type: TabType, agentId?: string, params?: Record<string, string>) => Tab | undefined;

  // Derived (flat accessors for backward compat)
  getActiveTab: () => Tab | undefined;
  getGroupTabs: (groupId: string) => Tab[];
  getAllTabs: () => Tab[];
}

const STORAGE_KEY = "axon-tabs";
const DEFAULT_GROUP = "main";

let nextId = 1;
function genId(prefix: string): string {
  return `${prefix}-${nextId++}-${Date.now().toString(36)}`;
}

function defaultState(): Pick<TabStore, "tabs" | "groups" | "splitRoot" | "activeGroupId"> {
  return {
    tabs: {},
    groups: { [DEFAULT_GROUP]: { id: DEFAULT_GROUP, tabs: [], activeTabId: null } },
    splitRoot: { type: "leaf", groupId: DEFAULT_GROUP },
    activeGroupId: DEFAULT_GROUP,
  };
}

interface PersistedState {
  tabs: Record<string, Tab>;
  groups: Record<string, TabGroup>;
  splitRoot: SplitNode;
  activeGroupId: string;
}

function persist(state: TabStore) {
  try {
    const data: PersistedState = {
      tabs: state.tabs,
      groups: state.groups,
      splitRoot: state.splitRoot,
      activeGroupId: state.activeGroupId,
    };
    localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
  } catch { /* ignore */ }
}

function loadState(): Pick<TabStore, "tabs" | "groups" | "splitRoot" | "activeGroupId"> {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return defaultState();
    const parsed = JSON.parse(raw);

    // Migrate from old flat format
    if (Array.isArray(parsed.tabs)) {
      return migrateFromFlat(parsed.tabs, parsed.activeTabId);
    }

    if (parsed.groups && parsed.splitRoot) {
      return parsed;
    }
  } catch { /* ignore */ }
  return defaultState();
}

/** Migrate from Phase 2 flat tab list to grouped format */
function migrateFromFlat(flatTabs: Omit<Tab, "groupId">[], activeTabId: string | null) {
  const state = defaultState();
  for (const t of flatTabs) {
    const tab: Tab = { ...t, groupId: DEFAULT_GROUP };
    state.tabs[tab.id] = tab;
    state.groups[DEFAULT_GROUP].tabs.push(tab.id);
  }
  state.groups[DEFAULT_GROUP].activeTabId = activeTabId;
  return state;
}

/** Remove a group from the split tree, collapsing parent branches */
function removeGroupFromTree(node: SplitNode, groupId: string): SplitNode | null {
  if (node.type === "leaf") {
    return node.groupId === groupId ? null : node;
  }
  const filtered: SplitNode[] = [];
  const sizes: number[] = [];
  for (let i = 0; i < node.children.length; i++) {
    const result = removeGroupFromTree(node.children[i], groupId);
    if (result) {
      filtered.push(result);
      sizes.push(node.sizes[i]);
    }
  }
  if (filtered.length === 0) return null;
  if (filtered.length === 1) return filtered[0];
  // Normalize sizes
  const total = sizes.reduce((a, b) => a + b, 0);
  return { ...node, children: filtered, sizes: sizes.map((s) => s / total * 100) };
}

/** Find the parent branch and index of a group in the split tree */
function findGroupInTree(node: SplitNode, groupId: string, path: number[] = []): number[] | null {
  if (node.type === "leaf") {
    return node.groupId === groupId ? path : null;
  }
  for (let i = 0; i < node.children.length; i++) {
    const result = findGroupInTree(node.children[i], groupId, [...path, i]);
    if (result) return result;
  }
  return null;
}

/** Get a node at a path in the split tree */
function getNodeAtPath(root: SplitNode, path: number[]): SplitNode {
  let node = root;
  for (const idx of path) {
    if (node.type !== "branch") break;
    node = node.children[idx];
  }
  return node;
}

/** Set sizes at a branch path */
function setSizesAtPath(root: SplitNode, path: number[], sizes: number[]): SplitNode {
  if (path.length === 0 && root.type === "branch") {
    return { ...root, sizes };
  }
  if (root.type !== "branch") return root;
  const [head, ...rest] = path;
  const children = [...root.children];
  if (rest.length === 0 && root.type === "branch") {
    return { ...root, sizes };
  }
  children[head] = setSizesAtPath(children[head], rest, sizes);
  return { ...root, children };
}

/** Replace a leaf node with a new branch */
function replaceLeafWithBranch(
  root: SplitNode,
  groupId: string,
  direction: SplitDirection,
  newGroupId: string,
): SplitNode {
  if (root.type === "leaf") {
    if (root.groupId === groupId) {
      return {
        type: "branch",
        direction,
        children: [
          { type: "leaf", groupId },
          { type: "leaf", groupId: newGroupId },
        ],
        sizes: [50, 50],
      };
    }
    return root;
  }
  return {
    ...root,
    children: root.children.map((c) => replaceLeafWithBranch(c, groupId, direction, newGroupId)),
  };
}

export const useTabStore = create<TabStore>((set, get) => {
  const initial = loadState();

  return {
    ...initial,
    tabDragging: false,
    setTabDragging: (v: boolean) => set({ tabDragging: v }),

    openTab: (tabDef, groupId) => {
      const state = get();
      const existing = state.findTab(tabDef.type, tabDef.agentId, tabDef.params);
      if (existing) {
        // Bail if already the active tab in the active group — no state change needed
        const group = state.groups[existing.groupId];
        if (
          state.activeGroupId === existing.groupId &&
          group?.activeTabId === existing.id
        ) {
          return existing.id;
        }
        // Activate existing tab and its group
        set({
          activeGroupId: existing.groupId,
          groups: {
            ...state.groups,
            [existing.groupId]: { ...group, activeTabId: existing.id },
          },
        });
        persist(get());
        return existing.id;
      }

      const targetGroupId = groupId || state.activeGroupId;
      const id = genId("tab");
      const newTab: Tab = { ...tabDef, id, groupId: targetGroupId };
      const group = state.groups[targetGroupId];

      set({
        tabs: { ...state.tabs, [id]: newTab },
        activeGroupId: targetGroupId,
        groups: {
          ...state.groups,
          [targetGroupId]: {
            ...group,
            tabs: [...group.tabs, id],
            activeTabId: id,
          },
        },
      });
      persist(get());
      return id;
    },

    closeTab: (tabId) => {
      const state = get();
      const tab = state.tabs[tabId];
      if (!tab) return;

      const group = state.groups[tab.groupId];
      const tabIdx = group.tabs.indexOf(tabId);
      const newTabIds = group.tabs.filter((id) => id !== tabId);

      // Determine new active tab for this group
      let newActiveId: string | null = group.activeTabId;
      if (newActiveId === tabId) {
        if (newTabIds.length === 0) {
          newActiveId = null;
        } else if (tabIdx >= newTabIds.length) {
          newActiveId = newTabIds[newTabIds.length - 1];
        } else {
          newActiveId = newTabIds[tabIdx];
        }
      }

      const newTabs = { ...state.tabs };
      delete newTabs[tabId];

      let newGroups = {
        ...state.groups,
        [tab.groupId]: { ...group, tabs: newTabIds, activeTabId: newActiveId },
      };

      let newSplitRoot = state.splitRoot;
      let newActiveGroupId = state.activeGroupId;

      // If group is now empty and it's not the last group, remove it
      if (newTabIds.length === 0 && Object.keys(newGroups).length > 1) {
        delete newGroups[tab.groupId];
        const cleaned = removeGroupFromTree(newSplitRoot, tab.groupId);
        newSplitRoot = cleaned || defaultState().splitRoot;

        if (newActiveGroupId === tab.groupId) {
          newActiveGroupId = Object.keys(newGroups)[0];
        }
      }

      set({
        tabs: newTabs,
        groups: newGroups,
        splitRoot: newSplitRoot,
        activeGroupId: newActiveGroupId,
      });
      persist(get());
    },

    closeOtherTabs: (tabId) => {
      const state = get();
      const tab = state.tabs[tabId];
      if (!tab) return;

      const group = state.groups[tab.groupId];
      const keep = group.tabs.filter((id) => id === tabId || state.tabs[id]?.pinned);
      const remove = group.tabs.filter((id) => !keep.includes(id));

      const newTabs = { ...state.tabs };
      for (const id of remove) delete newTabs[id];

      set({
        tabs: newTabs,
        groups: {
          ...state.groups,
          [tab.groupId]: { ...group, tabs: keep, activeTabId: tabId },
        },
      });
      persist(get());
    },

    closeAllTabs: () => {
      set(defaultState());
      persist(get());
    },

    activateTab: (tabId) => {
      const state = get();
      const tab = state.tabs[tabId];
      if (!tab) return;

      // Bail if already active
      const group = state.groups[tab.groupId];
      if (state.activeGroupId === tab.groupId && group?.activeTabId === tabId) return;

      set({
        activeGroupId: tab.groupId,
        groups: {
          ...state.groups,
          [tab.groupId]: { ...state.groups[tab.groupId], activeTabId: tabId },
        },
      });
      persist(get());
    },

    moveTab: (tabId, toIndex, targetGroupId) => {
      const state = get();
      const tab = state.tabs[tabId];
      if (!tab) return;

      const sourceGroupId = tab.groupId;
      const destGroupId = targetGroupId || sourceGroupId;

      if (sourceGroupId === destGroupId) {
        // Move within same group
        const group = state.groups[sourceGroupId];
        const tabIds = [...group.tabs];
        const fromIdx = tabIds.indexOf(tabId);
        if (fromIdx === -1 || fromIdx === toIndex) return;
        tabIds.splice(fromIdx, 1);
        tabIds.splice(toIndex, 0, tabId);
        set({
          groups: { ...state.groups, [sourceGroupId]: { ...group, tabs: tabIds } },
        });
      } else {
        // Move between groups
        const sourceGroup = state.groups[sourceGroupId];
        const destGroup = state.groups[destGroupId];
        const sourceTabs = sourceGroup.tabs.filter((id) => id !== tabId);
        const destTabs = [...destGroup.tabs];
        destTabs.splice(toIndex, 0, tabId);

        const newTab = { ...tab, groupId: destGroupId };
        let newSourceActive = sourceGroup.activeTabId;
        if (newSourceActive === tabId) {
          newSourceActive = sourceTabs.length > 0 ? sourceTabs[0] : null;
        }

        let newGroups = {
          ...state.groups,
          [sourceGroupId]: { ...sourceGroup, tabs: sourceTabs, activeTabId: newSourceActive },
          [destGroupId]: { ...destGroup, tabs: destTabs, activeTabId: tabId },
        };

        let newSplitRoot = state.splitRoot;
        let newActiveGroupId = destGroupId;

        // Clean up empty source group
        if (sourceTabs.length === 0 && Object.keys(newGroups).length > 1) {
          delete newGroups[sourceGroupId];
          const cleaned = removeGroupFromTree(newSplitRoot, sourceGroupId);
          newSplitRoot = cleaned || defaultState().splitRoot;
        }

        set({
          tabs: { ...state.tabs, [tabId]: newTab },
          groups: newGroups,
          splitRoot: newSplitRoot,
          activeGroupId: newActiveGroupId,
        });
      }
      persist(get());
    },

    pinTab: (tabId) => {
      const state = get();
      const tab = state.tabs[tabId];
      if (!tab) return;
      const group = state.groups[tab.groupId];
      const tabIds = [...group.tabs];
      // Move to front of group
      const idx = tabIds.indexOf(tabId);
      if (idx > 0) {
        tabIds.splice(idx, 1);
        tabIds.unshift(tabId);
      }
      set({
        tabs: { ...state.tabs, [tabId]: { ...tab, pinned: true } },
        groups: { ...state.groups, [tab.groupId]: { ...group, tabs: tabIds } },
      });
      persist(get());
    },

    unpinTab: (tabId) => {
      const state = get();
      const tab = state.tabs[tabId];
      if (!tab) return;
      set({ tabs: { ...state.tabs, [tabId]: { ...tab, pinned: false } } });
      persist(get());
    },

    updateTabLabel: (tabId, label) => {
      const state = get();
      const tab = state.tabs[tabId];
      if (!tab) return;
      set({ tabs: { ...state.tabs, [tabId]: { ...tab, label } } });
      persist(get());
    },

    splitGroup: (groupId, direction, tabId) => {
      const state = get();
      const newGroupId = genId("grp");
      const newGroup: TabGroup = { id: newGroupId, tabs: [], activeTabId: null };

      let newGroups = { ...state.groups, [newGroupId]: newGroup };
      let newTabs = state.tabs;

      // If a tabId is provided, move it to the new group
      if (tabId) {
        const tab = state.tabs[tabId];
        if (tab) {
          const sourceGroup = state.groups[tab.groupId];
          const sourceTabs = sourceGroup.tabs.filter((id) => id !== tabId);
          let newSourceActive = sourceGroup.activeTabId;
          if (newSourceActive === tabId) {
            newSourceActive = sourceTabs.length > 0 ? sourceTabs[0] : null;
          }
          newGroups = {
            ...newGroups,
            [tab.groupId]: { ...sourceGroup, tabs: sourceTabs, activeTabId: newSourceActive },
            [newGroupId]: { ...newGroup, tabs: [tabId], activeTabId: tabId },
          };
          newTabs = { ...state.tabs, [tabId]: { ...tab, groupId: newGroupId } };
        }
      }

      const newSplitRoot = replaceLeafWithBranch(state.splitRoot, groupId, direction, newGroupId);

      set({
        tabs: newTabs,
        groups: newGroups,
        splitRoot: newSplitRoot,
        activeGroupId: newGroupId,
      });
      persist(get());
      return newGroupId;
    },

    resizeSplit: (path, sizes) => {
      const state = get();
      // path points to the branch node whose sizes we're updating
      const parentPath = path.slice(0, -1);
      let node: SplitNode = state.splitRoot;
      for (const idx of parentPath) {
        if (node.type !== "branch") return;
        node = node.children[idx];
      }
      // Actually, path is the path to the branch itself
      const newRoot = setSizesAtPath(state.splitRoot, path, sizes);
      set({ splitRoot: newRoot });
      persist(get());
    },

    openAgentChat: (agentId, agentName) => {
      get().openTab({ type: "chat", label: agentName, agentId });
    },

    findTab: (type, agentId, params) => {
      const tabs = Object.values(get().tabs);
      return tabs.find((t) => {
        if (t.type !== type) return false;
        if (agentId !== undefined && t.agentId !== agentId) return false;
        if (params) {
          for (const [k, v] of Object.entries(params)) {
            if (t.params?.[k] !== v) return false;
          }
        }
        return true;
      });
    },

    getActiveTab: () => {
      const state = get();
      const group = state.groups[state.activeGroupId];
      if (!group?.activeTabId) return undefined;
      return state.tabs[group.activeTabId];
    },

    getGroupTabs: (groupId) => {
      const state = get();
      const group = state.groups[groupId];
      if (!group) return [];
      return group.tabs.map((id) => state.tabs[id]).filter(Boolean);
    },

    getAllTabs: () => {
      return Object.values(get().tabs);
    },
  };
});
