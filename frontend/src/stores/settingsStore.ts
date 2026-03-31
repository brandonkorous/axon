import { create } from "zustand";

export type SettingsTab =
  | "general"
  | "organization"
  | "models"
  | "agents"
  | "voice"
  | "credentials"
  | "extensions"
  | "host-agents";

interface Preferences {
  theme: string;
  voice_settings: Record<string, unknown>;
  display_prefs: Record<string, unknown>;
}

interface SettingsStore {
  isOpen: boolean;
  activeTab: SettingsTab;
  open: (tab?: SettingsTab) => void;
  close: () => void;
  setTab: (tab: SettingsTab) => void;

  // User preferences (synced with API)
  preferences: Preferences | null;
  prefsLoaded: boolean;
  fetchPreferences: () => Promise<void>;
  savePreferences: (patch: Partial<Preferences>) => Promise<void>;
}

export const useSettingsStore = create<SettingsStore>((set, get) => ({
  isOpen: false,
  activeTab: "general",
  open: (tab) => {
    set({ isOpen: true, activeTab: tab ?? "general" });
    // Fetch preferences on open if not yet loaded
    if (!get().prefsLoaded) get().fetchPreferences();
  },
  close: () => set({ isOpen: false }),
  setTab: (activeTab) => set({ activeTab }),

  preferences: null,
  prefsLoaded: false,

  fetchPreferences: async () => {
    try {
      const res = await fetch("/api/preferences");
      if (!res.ok) return;
      const data = await res.json();
      set({ preferences: data, prefsLoaded: true });
    } catch {
      // API unavailable — use defaults
    }
  },

  savePreferences: async (patch) => {
    try {
      const res = await fetch("/api/preferences", {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(patch),
      });
      if (!res.ok) return;
      const data = await res.json();
      set({ preferences: data });
    } catch {
      // API unavailable — changes still applied locally
    }
  },
}));
