# Axon IDE Layout Refactor — Implementation Plan

## Vision

Transform Axon's current sidebar + page navigation layout into a VS Code-style IDE layout with:
- **Left activity bar + collapsible panel** (navigation, agents, search)
- **Right collapsible panel** (agent toolbelt, config, context)
- **Center tabbed workspace** with drag-to-rearrange, split views (multi-column, multi-row)
- **Bottom collapsible output panel** (logs, task output, approvals)
- **Status bar** (unchanged, stays at bottom)

Default experience: Dashboard loads with a prominent chat window. Panels start collapsed. Power users expand as needed. Progressive disclosure.

---

## Current Architecture (What We're Replacing)

| Zone | Current | New |
|------|---------|-----|
| Left | 256px sidebar with all navigation | Activity bar (48px) + collapsible panel (256px) |
| Center | Single `<Outlet />` (full page swap via router) | Tabbed workspace with split groups |
| Right | ToolbeltSidebar (48px bar + 320px panel) | Collapsible panel (reuses toolbelt concept) |
| Bottom | Nothing (output lives inline in chat) | Collapsible output panel (logs, tasks, approvals) |
| Footer | StatusBar (28px) | StatusBar (unchanged) |

### Files Directly Affected
- `Layout.tsx` (227 lines) — complete rewrite into `LayoutShell`
- `App.tsx` (60 lines) — routes become tab-openable, not page-navigable
- `AgentView.tsx` (396 lines) — becomes a tab panel type, loses its own layout wrapper
- `AxonView.tsx` (401 lines) — becomes a tab panel type
- `DashboardView.tsx` (322 lines) — becomes default tab, or the "welcome" tab
- `ToolbeltSidebar.tsx` (113 lines) — migrates into right panel system
- `StatusBar.tsx` (63 lines) — minimal changes, stays as-is
- All other view components — wrapped as tab panel types (minimal changes per file)

### Stores Affected
- `toolbeltSidebarStore.ts` — absorbed into new `panelStore`
- New stores: `tabStore`, `panelStore`, `layoutStore`

---

## Architecture Design

### Layout Shell Zones

```
┌─────────────────────────────────────────────────────────────────┐
│ ┌──┬──────────┬────────────────────────────┬──────────┐         │
│ │  │          │  Tab Bar (group 1)         │          │         │
│ │  │          ├────────────────────────────┤          │         │
│ │A │  Left    │                            │  Right   │         │
│ │c │  Panel   │  Tab Content (group 1)     │  Panel   │         │
│ │t │          │                            │          │         │
│ │. │ (agents, ├────────────────────────────┤(toolbelt,│         │
│ │  │  search, │  Tab Bar (group 2)         │  config, │         │
│ │B │  nav)    ├────────────────────────────┤  context)│         │
│ │a │          │  Tab Content (group 2)     │          │         │
│ │r │          │                            │          │         │
│ ├──┼──────────┼────────────────────────────┼──────────┤         │
│ │  │          │  Bottom Panel              │          │         │
│ │  │          │  (output, logs, approvals) │          │         │
│ ├──┴──────────┴────────────────────────────┴──────────┤         │
│ │ Status Bar                                          │         │
│ └─────────────────────────────────────────────────────┘         │
└─────────────────────────────────────────────────────────────────┘
```

### Split Groups

The center workspace supports N split groups arranged in a grid. Each group has its own tab bar and content area. Users can:
- Drag a tab to create a new split (left/right/top/bottom of existing group)
- Drag a tab between groups
- Close a group by closing all its tabs
- Resize groups via drag handles between them

Split layout is stored as a tree:
```typescript
type SplitNode =
  | { type: 'leaf'; groupId: string }
  | { type: 'branch'; direction: 'horizontal' | 'vertical'; children: SplitNode[]; sizes: number[] };
```

### Tab System

```typescript
interface Tab {
  id: string;                    // unique tab id
  type: TabType;                 // 'chat' | 'document' | 'memory' | 'dashboard' | 'tasks' | ...
  label: string;                 // display name
  icon?: string;                 // tab icon
  agentId?: string;              // agent scope (if applicable)
  params?: Record<string, any>; // type-specific params (docPath, memoryNodeId, etc.)
  dirty?: boolean;               // unsaved changes indicator
  pinned?: boolean;              // pinned tabs stay left
}

type TabType =
  | 'chat'           // agent conversation (scoped to agentId)
  | 'axon'           // axon orchestrator chat
  | 'dashboard'      // command center
  | 'document'       // markdown/doc viewer
  | 'memory'         // memory tree / mind view
  | 'tasks'          // task board
  | 'calendar'       // calendar view
  | 'analytics'      // analytics dashboard
  | 'achievements'   // achievements view
  | 'approvals'      // approvals list
  | 'issues'         // issues list
  | 'org-chart'      // org chart
  | 'audit'          // audit log
  | 'usage'          // usage stats
  | 'plugins'        // plugin browser
  | 'skills'         // skills browser
  | 'sandboxes'      // sandbox manager
  | 'artifacts'      // artifact viewer
  | 'settings'       // settings (could stay modal or become tab)
  | 'sandbox-terminal' // live sandbox terminal output
  | 'huddle'         // multi-agent huddle
  | 'welcome'        // welcome/empty state tab
```

### Tab Store (`tabStore.ts`)

```typescript
interface TabGroup {
  id: string;
  tabs: Tab[];
  activeTabId: string | null;
}

interface TabStore {
  groups: Record<string, TabGroup>;
  splitRoot: SplitNode;
  activeGroupId: string;

  // Tab operations
  openTab: (tab: Omit<Tab, 'id'>, groupId?: string) => string;  // returns tab id
  closeTab: (tabId: string) => void;
  activateTab: (tabId: string) => void;
  moveTab: (tabId: string, targetGroupId: string, index?: number) => void;
  pinTab: (tabId: string) => void;
  unpinTab: (tabId: string) => void;

  // Group operations
  createGroup: () => string;
  removeGroup: (groupId: string) => void;
  setActiveGroup: (groupId: string) => void;

  // Split operations
  splitGroup: (groupId: string, direction: 'horizontal' | 'vertical', tabId?: string) => string;
  resizeSplit: (nodeId: string, sizes: number[]) => void;

  // Convenience
  openAgentChat: (agentId: string, agentName: string) => void;
  openDocument: (vaultId: string, path: string) => void;
  findTabByTypeAndParams: (type: TabType, params: Partial<Tab>) => Tab | null;
}
```

### Panel Store (`panelStore.ts`)

```typescript
type LeftPanelView = 'agents' | 'search' | 'nav' | 'extensions';
type RightPanelView = 'plugins' | 'skills' | 'sandboxes' | 'comms' | 'agent-config';
type BottomPanelView = 'output' | 'tasks' | 'approvals' | 'problems';

interface PanelStore {
  // Left panel
  leftOpen: boolean;
  leftView: LeftPanelView;
  leftWidth: number;        // persisted, resizable

  // Right panel
  rightOpen: boolean;
  rightView: RightPanelView;
  rightWidth: number;

  // Bottom panel
  bottomOpen: boolean;
  bottomView: BottomPanelView;
  bottomHeight: number;

  // Actions
  toggleLeft: () => void;
  toggleRight: () => void;
  toggleBottom: () => void;
  setLeftView: (view: LeftPanelView) => void;
  setRightView: (view: RightPanelView) => void;
  setBottomView: (view: BottomPanelView) => void;
  resizeLeft: (width: number) => void;
  resizeRight: (width: number) => void;
  resizeBottom: (height: number) => void;
}
```

### Layout Store (`layoutStore.ts`)

```typescript
interface LayoutStore {
  // Persisted layout state (localStorage)
  layout: SerializedLayout;

  saveLayout: () => void;
  restoreLayout: () => void;
  resetLayout: () => void;
}

interface SerializedLayout {
  panels: { leftWidth: number; rightWidth: number; bottomHeight: number; leftOpen: boolean; rightOpen: boolean; bottomOpen: boolean };
  splitRoot: SplitNode;
  groups: Record<string, { tabs: Tab[]; activeTabId: string | null }>;
  activeGroupId: string;
}
```

### Activity Bar

The activity bar is a narrow icon column (48px) on the far left. Clicking an icon either:
- Toggles the left panel open/closed (if same view)
- Switches the left panel to that view and opens it (if different view)

Icons (top-aligned):
- **Agents** — list of agents (default, like VS Code's explorer)
- **Search** — global search across conversations, docs, memories
- **Navigation** — full nav menu (current sidebar content, condensed)
- **Extensions** — plugins, skills, sandboxes

Icons (bottom-aligned):
- **Settings** — opens settings (tab or modal)
- **User/Org** — org switcher

### Navigation Changes

Currently, React Router drives full-page navigation. In the new model:
- **Router still exists** for URL ↔ tab state synchronization
- Opening a route (e.g., `/agent/atlas`) opens a tab, doesn't replace the page
- URL reflects the active tab: `/agent/atlas`, `/dashboard`, `/tasks`, `/doc/vault/path`
- Browser back/forward navigates tab history
- Direct URL access restores the tab (or opens it fresh)

### Bottom Panel: Output System

The bottom panel introduces a new concept: **output channels**. Each running process (agent chat, sandbox task, build) can write to an output channel.

```typescript
interface OutputChannel {
  id: string;
  label: string;                 // "Atlas — sandbox build", "Scout — web search"
  source: { agentId?: string; taskId?: string; sandboxId?: string };
  entries: OutputEntry[];
  level: 'info' | 'warn' | 'error';
}

interface OutputEntry {
  timestamp: number;
  level: 'info' | 'warn' | 'error' | 'debug';
  text: string;
}
```

The bottom panel shows:
- **Output** tab: dropdown to select channel, streams output in real-time
- **Tasks** tab: running/recent tasks across all agents (compact table)
- **Approvals** tab: pending approvals queue (currently a full page)
- **Problems** tab: aggregated issues/errors from agents

When a chat shows an inline indicator ("running sandbox..."), the corresponding output channel in the bottom panel shows the detailed logs. User chooses their depth.

### Right Panel: Agent Context

The right panel is contextual to the active tab:
- If the active tab is a **chat**, the right panel shows that agent's toolbelt (plugins, skills, sandboxes, comms) — same as current ToolbeltSidebar
- If the active tab is a **document**, the right panel could show backlinks, outline, metadata
- If the active tab is **tasks**, the right panel could show task detail
- If no contextual content, the right panel hides or shows a default view

This replaces the current `ToolbeltSidebar` component and its store.

---

## Implementation Phases

### Phase 1: Layout Shell & Panel System
**Goal:** Replace Layout.tsx with the new 5-zone shell. All existing content renders in center zone as single tab group.

**New Files:**
- `components/Layout/LayoutShell.tsx` — the 5-zone flex layout
- `components/Layout/ActivityBar.tsx` — left icon rail
- `components/Layout/LeftPanel.tsx` — collapsible left panel container
- `components/Layout/RightPanel.tsx` — collapsible right panel container
- `components/Layout/BottomPanel.tsx` — collapsible bottom panel container
- `components/Layout/ResizeHandle.tsx` — drag handle for panel resizing
- `stores/panelStore.ts` — panel open/close, view selection, sizes

**Modified Files:**
- `Layout.tsx` → gutted, replaced by `LayoutShell` import
- `App.tsx` → minimal route changes (still renders through Outlet for now)

**What Works After Phase 1:**
- Activity bar with icons on the left
- Left panel opens/closes with agent list, nav menu
- Right panel opens/closes (empty for now, placeholder)
- Bottom panel opens/closes (empty for now, placeholder)
- Center area still renders current router Outlet (no tabs yet)
- All panel sizes draggable and persisted to localStorage
- Status bar unchanged at bottom
- Mobile: panels become overlays with backdrop (same as current sidebar behavior)

**Estimated Scope:** ~600 lines new, ~200 lines modified

---

### Phase 2: Tab System (Single Group)
**Goal:** Center area gets a tab bar. Router navigation opens tabs instead of replacing content. Single tab group only (no splits yet).

**New Files:**
- `components/Layout/TabBar.tsx` — tab strip with close buttons, active indicator
- `components/Layout/TabContent.tsx` — renders the active tab's component
- `components/Layout/TabPanel.tsx` — wrapper that lazy-loads tab content by type
- `stores/tabStore.ts` — tab state, open/close/activate/reorder

**Modified Files:**
- `LayoutShell.tsx` — center zone now renders TabBar + TabContent instead of Outlet
- `App.tsx` — routes become tab openers (intercept NavLink clicks → `tabStore.openTab()`)
- `Layout/LeftPanel.tsx` — nav items call `openTab()` instead of `<NavLink>`
- All view components (AgentView, DashboardView, etc.) — remove their own layout wrappers (headers that duplicate the tab identity), keep content only

**Tab Behavior:**
- Clicking a nav item opens a tab (or activates existing tab of same type+params)
- Tabs show icon + label + close button
- Active tab highlighted
- Drag to reorder tabs within the bar
- Middle-click to close
- Right-click context menu: Close, Close Others, Close All, Pin
- Pinned tabs show icon only, stay left

**URL Synchronization:**
- Active tab updates the URL
- Browser navigation (back/forward) switches active tab
- Direct URL opens the corresponding tab

**What Works After Phase 2:**
- Full tab bar in center area
- All existing views render as tabs
- Navigation opens tabs instead of page swaps
- Tab reordering, close, pin
- URL ↔ tab sync
- Still single tab group (no splits)

**Estimated Scope:** ~500 lines new, ~400 lines modified

---

### Phase 3: Split View System
**Goal:** Users can split the center workspace into multiple tab groups arranged in a grid.

**New Files:**
- `components/Layout/SplitContainer.tsx` — recursive split tree renderer
- `components/Layout/SplitResizeHandle.tsx` — handles between split groups
- `components/Layout/DropZone.tsx` — visual drop targets when dragging tabs

**Modified Files:**
- `tabStore.ts` — add split tree state, group management, drag-to-split logic
- `TabBar.tsx` — drag start handler, drop target integration
- `LayoutShell.tsx` — center zone renders SplitContainer instead of single TabBar+TabContent

**Split Behavior:**
- Drag a tab toward an edge of a group → creates a new split
- Drop zones appear as translucent overlays (top/bottom/left/right/center)
- Dropping on center = move tab to that group
- Dropping on edge = create new group in that direction
- Resize handles between groups (horizontal and vertical)
- Closing all tabs in a group removes the group
- Minimum group size enforced

**What Works After Phase 3:**
- Drag tabs to create horizontal/vertical splits
- Multi-column, multi-row layouts
- Resize split groups
- Tabs move between groups freely
- Layout persists to localStorage

**Estimated Scope:** ~400 lines new, ~200 lines modified

---

### Phase 4: Bottom Panel — Output System
**Goal:** Bottom panel shows real-time output from running agents, tasks, and sandboxes.

**New Files:**
- `components/Layout/BottomPanel/OutputView.tsx` — output channel viewer with channel selector
- `components/Layout/BottomPanel/TasksView.tsx` — running/recent tasks table
- `components/Layout/BottomPanel/ApprovalsView.tsx` — compact approvals queue
- `components/Layout/BottomPanel/ProblemsView.tsx` — aggregated issues
- `stores/outputStore.ts` — output channel management

**Modified Files:**
- `BottomPanel.tsx` — renders the 4 sub-views based on active bottom tab
- `agentRuntimeStore.ts` — task logs feed into output channels
- `AgentView.tsx` (now a tab panel) — running task indicators link to bottom panel output
- WebSocket handlers — pipe detailed output to `outputStore`

**What Works After Phase 4:**
- Bottom panel has Output, Tasks, Approvals, Problems tabs
- Output channels stream real-time logs per agent/task/sandbox
- Inline chat indicators ("running...") correspond to selectable output channels
- Tasks tab shows running work across all agents
- Approvals tab replaces the full-page approvals view for quick actions

**Estimated Scope:** ~500 lines new, ~150 lines modified

---

### Phase 5: Right Panel — Contextual Sidebar
**Goal:** Right panel shows context-aware content based on the active tab.

**Modified Files:**
- `RightPanel.tsx` — renders content based on active tab type
- Move existing toolbelt content (from `AgentControls/`) into right panel sub-views
- `toolbeltSidebarStore.ts` — deprecated, state absorbed into `panelStore`
- `AgentView.tsx` — remove embedded ToolbeltSidebar (now in right panel)

**Context Rules:**
| Active Tab Type | Right Panel Content |
|----------------|---------------------|
| `chat` / `axon` | Agent toolbelt (plugins, skills, sandboxes, comms) |
| `document` | Document outline, backlinks, metadata |
| `tasks` | Selected task detail |
| `memory` | Memory node inspector |
| `dashboard` | Quick agent status / no panel |
| Other | Panel hidden or generic |

**What Works After Phase 5:**
- Right panel shows relevant context for whatever tab is active
- Agent toolbelt works same as before but in the right panel zone
- Documents show outline/backlinks in right panel
- Panel hides when no context available

**Estimated Scope:** ~300 lines new, ~200 lines modified

---

### Phase 6: Activity Bar & Left Panel Polish
**Goal:** Finalize the left activity bar and panel with all view modes.

**Modified Files:**
- `ActivityBar.tsx` — finalize icons, active states, badge counts
- `LeftPanel.tsx` — implement all 4 views

**Left Panel Views:**

**Agents View (default):**
- Agent list with status indicators (like VS Code file explorer)
- Click agent → opens chat tab
- Right-click → context menu (lifecycle actions, open memory, etc.)
- Collapsible sections: Active, Idle, All
- Inline status: thinking, running task, idle

**Search View:**
- Global search input
- Searches across: conversations, documents, memories, tasks, issues
- Results grouped by type
- Click result → opens in appropriate tab

**Navigation View:**
- Condensed version of current sidebar nav
- All the same links but opens tabs instead
- Badge counts for approvals, issues

**Extensions View:**
- Installed plugins, skills, sandbox images
- Quick enable/disable toggles

**What Works After Phase 6:**
- Activity bar fully functional with all 4 views
- Agent list with rich status and context menus
- Global search opens results in tabs
- Full navigation available from left panel

**Estimated Scope:** ~400 lines new, ~150 lines modified

---

### Phase 7: Keyboard Shortcuts & Polish
**Goal:** VS Code-style keyboard shortcuts, layout persistence, animation polish.

**Keyboard Shortcuts:**
- `Ctrl+B` — toggle left panel
- `Ctrl+J` — toggle bottom panel
- `Ctrl+Shift+B` — toggle right panel (or a custom binding)
- `Ctrl+\` — split editor
- `Ctrl+W` — close active tab
- `Ctrl+Tab` — cycle tabs
- `Ctrl+Shift+Tab` — cycle tabs reverse
- `Ctrl+1/2/3` — focus split group 1/2/3
- `Ctrl+P` — quick open (search for tab type, agent, document)
- `Ctrl+Shift+P` — command palette (stretch goal)

**Polish:**
- Smooth panel open/close animations (Framer Motion)
- Tab drag preview ghost
- Drop zone highlight animations
- Panel resize cursor feedback
- Empty state for each panel view
- Mobile responsive: panels become sheet overlays
- Layout fully persisted and restored on refresh
- "Reset Layout" option in settings/command palette

**Estimated Scope:** ~300 lines new, ~200 lines modified

---

## Migration Strategy

### Router Migration

Current routes don't disappear — they become tab openers:

```typescript
// Before (App.tsx)
<Route path="/agent/:agentId" element={<AgentView />} />

// After (App.tsx still defines routes for URL sync)
<Route path="/agent/:agentId" element={<TabRedirect type="chat" />} />

// TabRedirect reads params, calls tabStore.openTab(), renders nothing
```

The `<Outlet />` in the old Layout is replaced by the tab content area. Routes exist purely for URL ↔ tab synchronization.

### Component Migration

Each existing view component needs minimal changes:
1. Remove any layout wrapper (flex h-full containers that assume full page)
2. Accept optional props from the tab system (most already use URL params or stores)
3. Export a `tabType` registration with icon and label

Example:
```typescript
// Before: AgentView owns its full layout
export function AgentView() {
  return (
    <div className="flex flex-col h-full">
      <header>...</header>
      <main>...</main>
      <ChatInput />
    </div>
  );
}

// After: AgentView is just content, tab system provides the container
export function AgentView({ agentId }: { agentId: string }) {
  return (
    <div className="flex flex-col h-full">
      {/* header simplified — tab already shows agent name */}
      <main>...</main>
      <ChatInput />
    </div>
  );
}

// Tab type registration
registerTabType('chat', {
  icon: MessageSquare,
  label: (params) => params.agentName || 'Chat',
  component: AgentView,
  propsFromTab: (tab) => ({ agentId: tab.agentId }),
});
```

### Store Migration

- `toolbeltSidebarStore` → state moves to `panelStore.rightOpen`, `panelStore.rightView`
- `settingsStore` → settings could become a tab type (Phase 2) or stay as modal
- All other stores remain unchanged — they're data stores, not layout stores

---

## Default Layout State

On first load (no persisted layout):

```
┌──┬─────────────────────────────────────┐
│  │  [Dashboard]                        │
│A │                                     │
│c │  Dashboard content                  │
│t │  with prominent agent cards         │
│. │  and quick-chat entry point         │
│  │                                     │
│B │                                     │
│a │                                     │
│r │                                     │
├──┴─────────────────────────────────────┤
│ Status Bar                             │
└────────────────────────────────────────┘
```

- Left panel: collapsed (activity bar visible)
- Right panel: collapsed
- Bottom panel: collapsed
- Center: single group, single tab (Dashboard)
- Clicking an agent opens a chat tab, the dashboard tab stays open

---

## File Structure (New)

```
src/components/Layout/
├── LayoutShell.tsx          — root 5-zone layout
├── ActivityBar.tsx          — left icon rail
├── LeftPanel.tsx            — collapsible left panel container
├── LeftPanel/
│   ├── AgentsView.tsx       — agent list with status
│   ├── SearchView.tsx       — global search
│   ├── NavigationView.tsx   — condensed nav menu
│   └── ExtensionsView.tsx   — plugins/skills/sandboxes list
├── RightPanel.tsx           — collapsible right panel container
├── RightPanel/
│   ├── AgentToolbelt.tsx    — migrated from ToolbeltSidebar
│   ├── DocumentOutline.tsx  — doc backlinks/outline
│   └── TaskDetail.tsx       — task inspector
├── BottomPanel.tsx          — collapsible bottom panel container
├── BottomPanel/
│   ├── OutputView.tsx       — output channel viewer
│   ├── TasksView.tsx        — running tasks table
│   ├── ApprovalsView.tsx    — compact approvals
│   └── ProblemsView.tsx     — issues/errors
├── TabBar.tsx               — tab strip
├── TabContent.tsx           — active tab renderer
├── TabPanel.tsx             — lazy-loads tab component by type
├── TabRegistry.ts           — tab type definitions and component map
├── SplitContainer.tsx       — recursive split tree renderer
├── SplitResizeHandle.tsx    — split group resize handle
├── ResizeHandle.tsx         — panel resize handle
├── DropZone.tsx             — tab drag drop targets
└── TabRedirect.tsx          — route → tab opener bridge

src/stores/
├── tabStore.ts              — tabs, groups, splits, active state
├── panelStore.ts            — left/right/bottom panel state
├── layoutStore.ts           — serialization/persistence
├── outputStore.ts           — output channels for bottom panel
└── (existing stores unchanged)
```

---

## Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| Large refactor breaks existing features | Phase 1 keeps existing Outlet rendering. Each phase is independently shippable. |
| Split view complexity explodes | Start with simple horizontal/vertical splits. No arbitrary grid until proven needed. |
| Performance with many open tabs | Lazy-mount tab content (only active tab in each group is rendered). Unmount tabs that haven't been viewed in 5+ minutes. |
| Mobile responsiveness | Panels become sheet overlays. Splits disabled on mobile (single tab only). Tab bar scrolls horizontally. |
| URL sync complexity | Keep it simple: URL reflects active tab only. Split state is not in URL (persisted to localStorage). |
| WebSocket connections per chat tab | Already managed by agentId — opening a second tab for same agent reuses the connection. |

---

## Phase Summary

| Phase | Deliverable | Depends On | New Lines (est.) |
|-------|------------|------------|------------------|
| 1 | Layout Shell & Panel System | — | ~800 |
| 2 | Tab System (Single Group) | Phase 1 | ~900 |
| 3 | Split View System | Phase 2 | ~600 |
| 4 | Bottom Panel Output System | Phase 1 | ~650 |
| 5 | Right Panel Contextual Sidebar | Phase 2 | ~500 |
| 6 | Activity Bar & Left Panel Polish | Phase 2 | ~550 |
| 7 | Keyboard Shortcuts & Polish | All | ~500 |

Phases 4, 5, 6 can run in parallel after Phase 2 is complete.

**Total estimated new code: ~4,500 lines**
**Total estimated modified code: ~1,500 lines**
