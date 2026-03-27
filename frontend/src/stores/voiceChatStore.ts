import { create } from "zustand";

export type VoiceState = "idle" | "listening" | "processing" | "speaking";

function stored(key: string, fallback: number): number {
  return parseFloat(localStorage.getItem(key) ?? String(fallback));
}

function storedStr(key: string, fallback: string): string {
  return localStorage.getItem(key) ?? fallback;
}

function storedBool(key: string, fallback: boolean): boolean {
  const v = localStorage.getItem(key);
  return v === null ? fallback : v === "true";
}

/** Fire-and-forget sync of voice settings to the preferences API. */
function syncVoiceToApi() {
  const voice_settings = {
    sensitivity: parseFloat(localStorage.getItem("axon-mic-sensitivity") ?? "0.5"),
    silenceTimeout: parseFloat(localStorage.getItem("axon-silence-timeout") ?? "1500"),
    playbackSpeed: parseFloat(localStorage.getItem("axon-playback-speed") ?? "1"),
    autoInterrupt: localStorage.getItem("axon-auto-interrupt") !== "false",
    selectedVoice: localStorage.getItem("axon-selected-voice") ?? "",
  };
  fetch("/api/preferences", {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ voice_settings }),
  }).catch(() => {});
}

interface VoiceChatStore {
  // UI
  isOpen: boolean;
  open: () => void;
  close: () => void;

  // Settings modal
  settingsOpen: boolean;
  openSettings: () => void;
  closeSettings: () => void;

  // Voice pipeline
  voiceState: VoiceState;
  setVoiceState: (s: VoiceState) => void;

  // Mute (mic stays open but VAD ignores input)
  muted: boolean;
  setMuted: (v: boolean) => void;

  // Mic sensitivity (0–1, default 0.5). Higher = less sensitive (ignores more noise).
  sensitivity: number;
  setSensitivity: (v: number) => void;

  // Silence timeout (ms) — how long to wait after speech stops before sending
  silenceTimeout: number;
  setSilenceTimeout: (v: number) => void;

  // Playback speed (0.5–2.0)
  playbackSpeed: number;
  setPlaybackSpeed: (v: number) => void;

  // Auto-interrupt — whether speaking over AI cuts playback
  autoInterrupt: boolean;
  setAutoInterrupt: (v: boolean) => void;

  // Selected TTS voice (Piper voice key, empty = agent default)
  selectedVoice: string;
  setSelectedVoice: (v: string) => void;

  // Audio amplitude (0–1, updated at ~30fps by analyser)
  amplitude: number;
  setAmplitude: (v: number) => void;

  // Connection
  connected: boolean;
  setConnected: (v: boolean) => void;
}

export const useVoiceChatStore = create<VoiceChatStore>((set) => ({
  isOpen: false,
  open: () => set({ isOpen: true }),
  close: () =>
    set({
      isOpen: false,
      voiceState: "idle",
      muted: false,
      amplitude: 0,
      connected: false,
    }),

  settingsOpen: false,
  openSettings: () => set({ settingsOpen: true }),
  closeSettings: () => set({ settingsOpen: false }),

  voiceState: "idle",
  setVoiceState: (voiceState) => set({ voiceState }),

  muted: false,
  setMuted: (muted) => set({ muted }),

  sensitivity: stored("axon-mic-sensitivity", 0.5),
  setSensitivity: (sensitivity) => {
    localStorage.setItem("axon-mic-sensitivity", String(sensitivity));
    set({ sensitivity });
    syncVoiceToApi();
  },

  silenceTimeout: stored("axon-silence-timeout", 1500),
  setSilenceTimeout: (silenceTimeout) => {
    localStorage.setItem("axon-silence-timeout", String(silenceTimeout));
    set({ silenceTimeout });
    syncVoiceToApi();
  },

  playbackSpeed: stored("axon-playback-speed", 1.0),
  setPlaybackSpeed: (playbackSpeed) => {
    localStorage.setItem("axon-playback-speed", String(playbackSpeed));
    set({ playbackSpeed });
    syncVoiceToApi();
  },

  autoInterrupt: storedBool("axon-auto-interrupt", true),
  setAutoInterrupt: (autoInterrupt) => {
    localStorage.setItem("axon-auto-interrupt", String(autoInterrupt));
    set({ autoInterrupt });
    syncVoiceToApi();
  },

  selectedVoice: storedStr("axon-selected-voice", ""),
  setSelectedVoice: (selectedVoice) => {
    localStorage.setItem("axon-selected-voice", selectedVoice);
    set({ selectedVoice });
    syncVoiceToApi();
  },

  amplitude: 0,
  setAmplitude: (amplitude) => set({ amplitude }),

  connected: false,
  setConnected: (connected) => set({ connected }),
}));
