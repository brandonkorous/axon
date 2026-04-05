import { create } from "zustand";

export interface OutputEntry {
  timestamp: number;
  level: "info" | "warn" | "error" | "debug";
  text: string;
}

export interface OutputChannel {
  id: string;
  label: string;
  source: { agentId?: string; taskId?: string; sandboxId?: string };
  entries: OutputEntry[];
  maxLevel: "info" | "warn" | "error" | "debug";
}

interface OutputStore {
  channels: Record<string, OutputChannel>;
  activeChannelId: string | null;

  createChannel: (id: string, label: string, source: OutputChannel["source"]) => void;
  appendOutput: (channelId: string, text: string, level?: OutputEntry["level"]) => void;
  clearChannel: (channelId: string) => void;
  removeChannel: (channelId: string) => void;
  setActiveChannel: (channelId: string) => void;
  getChannelList: () => OutputChannel[];
}

const MAX_ENTRIES_PER_CHANNEL = 500;

export const useOutputStore = create<OutputStore>((set, get) => ({
  channels: {},
  activeChannelId: null,

  createChannel: (id, label, source) => {
    set((s) => ({
      channels: {
        ...s.channels,
        [id]: { id, label, source, entries: [], maxLevel: "info" },
      },
      activeChannelId: s.activeChannelId ?? id,
    }));
  },

  appendOutput: (channelId, text, level = "info") => {
    set((s) => {
      const channel = s.channels[channelId];
      if (!channel) return s;

      const entry: OutputEntry = { timestamp: Date.now(), level, text };
      let entries = [...channel.entries, entry];
      if (entries.length > MAX_ENTRIES_PER_CHANNEL) {
        entries = entries.slice(-MAX_ENTRIES_PER_CHANNEL);
      }

      const levelPriority = { debug: 0, info: 1, warn: 2, error: 3 };
      const maxLevel = levelPriority[level] > levelPriority[channel.maxLevel]
        ? level : channel.maxLevel;

      return {
        channels: {
          ...s.channels,
          [channelId]: { ...channel, entries, maxLevel },
        },
      };
    });
  },

  clearChannel: (channelId) => {
    set((s) => {
      const channel = s.channels[channelId];
      if (!channel) return s;
      return {
        channels: {
          ...s.channels,
          [channelId]: { ...channel, entries: [], maxLevel: "info" },
        },
      };
    });
  },

  removeChannel: (channelId) => {
    set((s) => {
      const { [channelId]: _, ...rest } = s.channels;
      return {
        channels: rest,
        activeChannelId: s.activeChannelId === channelId
          ? Object.keys(rest)[0] || null
          : s.activeChannelId,
      };
    });
  },

  setActiveChannel: (channelId) => {
    set({ activeChannelId: channelId });
  },

  getChannelList: () => {
    return Object.values(get().channels);
  },
}));
