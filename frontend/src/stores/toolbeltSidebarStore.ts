import { create } from "zustand";

export type SidebarTab = "plugins" | "skills" | "sandboxes" | "comms";

interface ToolbeltSidebarStore {
  isOpen: boolean;
  activeTab: SidebarTab;
  toggle: () => void;
  open: (tab?: SidebarTab) => void;
  close: () => void;
  setTab: (tab: SidebarTab) => void;
}

export const useToolbeltSidebarStore = create<ToolbeltSidebarStore>((set) => ({
  isOpen: false,
  activeTab: "plugins",
  toggle: () => set((s) => ({ isOpen: !s.isOpen })),
  open: (tab) =>
    set((s) => ({ isOpen: true, activeTab: tab ?? s.activeTab })),
  close: () => set({ isOpen: false }),
  setTab: (tab) => set({ activeTab: tab, isOpen: true }),
}));
