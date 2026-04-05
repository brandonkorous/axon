import { create } from "zustand";

export type LeftPanelView = "agents" | "search" | "nav" | "extensions";
export type RightPanelView = "plugins" | "skills" | "sandboxes" | "comms" | "agent-config";
export type BottomPanelView = "output" | "tasks" | "approvals" | "problems";

const STORAGE_KEY = "axon-panel-layout";

interface PanelSizes {
  leftWidth: number;
  rightWidth: number;
  bottomHeight: number;
}

interface PanelState {
  leftOpen: boolean;
  leftView: LeftPanelView;
  rightOpen: boolean;
  rightView: RightPanelView;
  bottomOpen: boolean;
  bottomView: BottomPanelView;
  sizes: PanelSizes;
}

interface PanelStore extends PanelState {
  toggleLeft: () => void;
  toggleRight: () => void;
  toggleBottom: () => void;
  setLeftView: (view: LeftPanelView) => void;
  setRightView: (view: RightPanelView) => void;
  setBottomView: (view: BottomPanelView) => void;
  resizeLeft: (width: number) => void;
  resizeRight: (width: number) => void;
  resizeBottom: (height: number) => void;
  closeAll: () => void;
}

const DEFAULTS: PanelState = {
  leftOpen: false,
  leftView: "agents",
  rightOpen: false,
  rightView: "plugins",
  bottomOpen: false,
  bottomView: "output",
  sizes: { leftWidth: 256, rightWidth: 320, bottomHeight: 200 },
};

const MIN_LEFT = 200;
const MAX_LEFT = 480;
const MIN_RIGHT = 240;
const MAX_RIGHT = 480;
const MIN_BOTTOM = 120;
const MAX_BOTTOM = 500;

function clamp(val: number, min: number, max: number) {
  return Math.max(min, Math.min(max, val));
}

function loadPersistedState(): Partial<PanelState> {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return {};
    return JSON.parse(raw);
  } catch {
    return {};
  }
}

function persistState(state: PanelState) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({
      leftOpen: state.leftOpen,
      leftView: state.leftView,
      rightOpen: state.rightOpen,
      rightView: state.rightView,
      bottomOpen: state.bottomOpen,
      bottomView: state.bottomView,
      sizes: state.sizes,
    }));
  } catch { /* localStorage full or unavailable */ }
}

export const usePanelStore = create<PanelStore>((set, get) => {
  const persisted = loadPersistedState();
  const initial: PanelState = { ...DEFAULTS, ...persisted };

  return {
    ...initial,

    toggleLeft: () => {
      set((s) => ({ leftOpen: !s.leftOpen }));
      persistState(get());
    },

    toggleRight: () => {
      set((s) => ({ rightOpen: !s.rightOpen }));
      persistState(get());
    },

    toggleBottom: () => {
      set((s) => ({ bottomOpen: !s.bottomOpen }));
      persistState(get());
    },

    setLeftView: (view) => {
      set((s) => {
        // If same view clicked, toggle panel
        if (s.leftOpen && s.leftView === view) return { leftOpen: false };
        return { leftView: view, leftOpen: true };
      });
      persistState(get());
    },

    setRightView: (view) => {
      set((s) => {
        if (s.rightOpen && s.rightView === view) return { rightOpen: false };
        return { rightView: view, rightOpen: true };
      });
      persistState(get());
    },

    setBottomView: (view) => {
      set((s) => {
        if (s.bottomOpen && s.bottomView === view) return { bottomOpen: false };
        return { bottomView: view, bottomOpen: true };
      });
      persistState(get());
    },

    resizeLeft: (width) => {
      const clamped = clamp(width, MIN_LEFT, MAX_LEFT);
      set((s) => ({ sizes: { ...s.sizes, leftWidth: clamped } }));
      persistState(get());
    },

    resizeRight: (width) => {
      const clamped = clamp(width, MIN_RIGHT, MAX_RIGHT);
      set((s) => ({ sizes: { ...s.sizes, rightWidth: clamped } }));
      persistState(get());
    },

    resizeBottom: (height) => {
      const clamped = clamp(height, MIN_BOTTOM, MAX_BOTTOM);
      set((s) => ({ sizes: { ...s.sizes, bottomHeight: clamped } }));
      persistState(get());
    },

    closeAll: () => {
      set({ leftOpen: false, rightOpen: false, bottomOpen: false });
      persistState(get());
    },
  };
});
