import { motion, AnimatePresence } from "framer-motion";
import { useVoiceChatStore } from "../../stores/voiceChatStore";

const EASE_OUT_QUART = [0.25, 1, 0.5, 1] as const;

export function VoiceChatFAB() {
  const isOpen = useVoiceChatStore((s) => s.isOpen);
  const { open } = useVoiceChatStore();

  return (
    <AnimatePresence>
      {!isOpen && (
        <motion.button
          key="voice-fab"
          initial={{ scale: 0, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ scale: 0, opacity: 0 }}
          transition={{ duration: 0.3, ease: EASE_OUT_QUART }}
          whileHover={{ scale: 1.08 }}
          whileTap={{ scale: 0.92 }}
          onClick={open}
          className="fixed z-40 bottom-12 right-6 w-14 h-14 rounded-full flex items-center justify-center bg-gradient-to-br from-primary to-primary/70 text-primary-content shadow-lg shadow-primary/25 hover:shadow-primary/40"
          aria-label="Voice chat with Axon"
        >
          {/* Breathing glow ring */}
          <motion.span
            className="absolute inset-0 rounded-full bg-primary/20 pointer-events-none"
            animate={{ scale: [1, 1.35, 1], opacity: [0.4, 0, 0.4] }}
            transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
            aria-hidden
          />
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" className="w-6 h-6 relative z-10">
            <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" />
            <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
            <line x1="12" y1="19" x2="12" y2="23" />
            <line x1="8" y1="23" x2="16" y2="23" />
          </svg>
        </motion.button>
      )}
    </AnimatePresence>
  );
}
