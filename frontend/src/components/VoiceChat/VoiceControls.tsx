import { motion, AnimatePresence } from "framer-motion";
import { useVoiceChatStore } from "../../stores/voiceChatStore";
import { useSettingsStore } from "../../stores/settingsStore";

const ICON_TRANSITION = { duration: 0.15, ease: [0.25, 1, 0.5, 1] as const };

function MicIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" className="w-6 h-6">
      <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" />
      <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
      <line x1="12" y1="19" x2="12" y2="23" />
      <line x1="8" y1="23" x2="16" y2="23" />
    </svg>
  );
}

function MicOffIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" className="w-6 h-6">
      <line x1="1" y1="1" x2="23" y2="23" />
      <path d="M9 9v3a3 3 0 0 0 5.12 2.12M15 9.34V4a3 3 0 0 0-5.94-.6" />
      <path d="M17 16.95A7 7 0 0 1 5 12v-2m14 0v2c0 .76-.12 1.49-.34 2.18" />
      <line x1="12" y1="19" x2="12" y2="23" />
      <line x1="8" y1="23" x2="16" y2="23" />
    </svg>
  );
}

export function VoiceControls() {
  const close = useVoiceChatStore((s) => s.close);
  const muted = useVoiceChatStore((s) => s.muted);
  const setMuted = useVoiceChatStore((s) => s.setMuted);
  const openSettings = useSettingsStore((s) => s.open);

  return (
    <div className="flex items-center justify-center gap-6 px-4 py-3 flex-shrink-0">
      <motion.button
        onClick={close}
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.9 }}
        transition={ICON_TRANSITION}
        className="btn btn-ghost btn-circle min-h-[44px] min-w-[44px] md:btn-sm"
        aria-label="Close voice chat"
      >
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} className="w-5 h-5">
          <path d="M18 6L6 18M6 6l12 12" />
        </svg>
      </motion.button>

      <motion.button
        onClick={() => setMuted(!muted)}
        whileTap={{ scale: 0.9 }}
        transition={ICON_TRANSITION}
        className="w-14 h-14 rounded-full flex items-center justify-center relative overflow-hidden focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 focus-visible:ring-offset-base-200"
        aria-label={muted ? "Unmute microphone" : "Mute microphone"}
      >
        {/* Animated background */}
        <motion.span
          className="absolute inset-0 rounded-full pointer-events-none"
          animate={
            muted
              ? { backgroundColor: "oklch(0.637 0.237 25.331 / 0.2)", borderColor: "oklch(0.637 0.237 25.331 / 0.3)" }
              : { backgroundColor: "oklch(0.541 0.281 293.009)", borderColor: "oklch(0.541 0.281 293.009)" }
          }
          transition={{ duration: 0.25, ease: [0.25, 1, 0.5, 1] }}
          style={{ border: "1px solid" }}
          aria-hidden
        />
        {/* Shadow for unmuted state */}
        <motion.span
          className="absolute inset-0 rounded-full pointer-events-none"
          animate={{ opacity: muted ? 0 : 1 }}
          transition={{ duration: 0.25 }}
          style={{ boxShadow: "0 10px 15px -3px oklch(0.541 0.281 293.009 / 0.2)" }}
          aria-hidden
        />
        {/* Icon crossfade */}
        <AnimatePresence mode="wait" initial={false}>
          <motion.span
            key={muted ? "off" : "on"}
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.8 }}
            transition={{ duration: 0.12 }}
            className={`relative z-10 flex items-center justify-center ${muted ? "text-error" : "text-primary-content"}`}
          >
            {muted ? <MicOffIcon /> : <MicIcon />}
          </motion.span>
        </AnimatePresence>
      </motion.button>

      <motion.button
        onClick={() => openSettings("voice")}
        whileHover={{ scale: 1.1, rotate: 30 }}
        whileTap={{ scale: 0.9 }}
        transition={ICON_TRANSITION}
        className="btn btn-ghost btn-circle min-h-[44px] min-w-[44px] md:btn-sm"
        aria-label="Voice settings"
      >
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" className="w-5 h-5">
          <circle cx="12" cy="12" r="3" />
          <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z" />
        </svg>
      </motion.button>
    </div>
  );
}
