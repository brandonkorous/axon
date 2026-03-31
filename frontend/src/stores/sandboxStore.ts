import { create } from "zustand";
import { orgApiPath, orgWsPath } from "./orgStore";

export type SandboxImageStatus = "idle" | "building" | "ready" | "error";

export interface SandboxImageInfo {
  type: string;
  description: string;
  estimated_size_mb: number;
  tools: string[];
  parent_type: string | null;
  status: SandboxImageStatus;
  size_mb: number | null;
  agents_using: string[];
  plugins_requiring: string[];
  progress_lines?: string[];
  started_at?: number | null;
  completed_at?: number | null;
  error?: string | null;
}

export interface RunningInstance {
  instance_id: string;
  instance_name: string;
  plugin: string;
  agents: string[];
  sandbox_id: string;
  status: "running" | "stopped";
}

interface SandboxStore {
  images: SandboxImageInfo[];
  runningInstances: RunningInstance[];
  loading: boolean;
  buildProgress: Record<string, string[]>;
  activeSockets: Record<string, WebSocket>;

  fetchImages: () => Promise<void>;
  fetchRunningInstances: () => Promise<void>;
  stopInstance: (instanceId: string) => Promise<boolean>;
  buildImage: (type: string) => Promise<boolean>;
  removeImage: (type: string) => Promise<boolean>;
  subscribeBuildProgress: (type: string, onComplete?: () => void) => void;
  unsubscribeBuildProgress: (type: string) => void;
}

export const useSandboxStore = create<SandboxStore>((set, get) => ({
  images: [],
  runningInstances: [],
  loading: false,
  buildProgress: {},
  activeSockets: {},

  fetchRunningInstances: async () => {
    try {
      const res = await fetch(orgApiPath("sandbox/running"));
      const data = await res.json();
      set({ runningInstances: data.instances || [] });
    } catch {
      // ignore
    }
  },

  stopInstance: async (instanceId) => {
    try {
      const res = await fetch(orgApiPath(`sandbox/running/${instanceId}/stop`), {
        method: "POST",
      });
      if (res.ok) {
        set((s) => ({
          runningInstances: s.runningInstances.filter((i) => i.instance_id !== instanceId),
        }));
        return true;
      }
      return false;
    } catch {
      return false;
    }
  },

  fetchImages: async () => {
    const hadImages = get().images.length > 0;
    if (!hadImages) set({ loading: true });
    try {
      const res = await fetch(orgApiPath("sandbox/images"));
      const data = await res.json();
      set({ images: data.images || [], loading: false });
    } catch {
      set({ loading: false });
    }
  },

  buildImage: async (type) => {
    try {
      const res = await fetch(orgApiPath(`sandbox/images/${type}/build`), {
        method: "POST",
      });
      if (res.ok) {
        // Optimistically set status to building
        const images = get().images.map((img) =>
          img.type === type ? { ...img, status: "building" as const } : img,
        );
        set({ images });
        return true;
      }
      return false;
    } catch {
      return false;
    }
  },

  removeImage: async (type) => {
    try {
      const res = await fetch(orgApiPath(`sandbox/images/${type}`), {
        method: "DELETE",
      });
      if (res.ok) {
        const images = get().images.map((img) =>
          img.type === type
            ? { ...img, status: "idle" as const, size_mb: null }
            : img,
        );
        set({ images });
        return true;
      }
      return false;
    } catch {
      return false;
    }
  },

  subscribeBuildProgress: (type, onComplete) => {
    const existing = get().activeSockets[type];
    if (existing?.readyState === WebSocket.OPEN) return;

    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const host = import.meta.env.DEV ? "127.0.0.1:8000" : window.location.host;
    const path = orgWsPath(`sandbox/images/${type}/build/stream`);
    const ws = new WebSocket(`${protocol}//${host}${path}`);

    set((s) => ({
      activeSockets: { ...s.activeSockets, [type]: ws },
      buildProgress: { ...s.buildProgress, [type]: [] },
    }));

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        if (msg.type === "progress") {
          set((s) => ({
            buildProgress: {
              ...s.buildProgress,
              [type]: [...(s.buildProgress[type] || []), msg.line],
            },
          }));
        } else if (msg.type === "complete" || msg.type === "error") {
          get().fetchImages();
          onComplete?.();
        }
      } catch {
        // ignore non-JSON
      }
    };

    ws.onclose = () => {
      set((s) => {
        const { [type]: _, ...rest } = s.activeSockets;
        return { activeSockets: rest };
      });
    };
  },

  unsubscribeBuildProgress: (type) => {
    const ws = get().activeSockets[type];
    if (ws) {
      ws.close();
      set((s) => {
        const { [type]: _, ...rest } = s.activeSockets;
        return { activeSockets: rest };
      });
    }
  },
}));
