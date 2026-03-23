import { useCallback, useEffect, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useVoiceChatStore } from "../../stores/voiceChatStore";
import { useConversationStore } from "../../stores/conversationStore";
import { useWebSocket } from "../../hooks/useWebSocket";
import { useVoiceContinuous } from "../../hooks/useVoiceContinuous";
import { useAudioPlayback } from "../../hooks/useAudioPlayback";
import { SparkleOrb } from "./SparkleOrb";
import { VoiceControls } from "./VoiceControls";

const AXON_CONVERSATION_ID = "axon";

function speakWithBrowser(text: string): Promise<void> {
  return new Promise((resolve) => {
    if (!window.speechSynthesis) {
      resolve();
      return;
    }
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = useVoiceChatStore.getState().playbackSpeed;
    utterance.pitch = 1;
    utterance.onend = () => resolve();
    utterance.onerror = () => resolve();
    window.speechSynthesis.speak(utterance);
  });
}

function cancelBrowserSpeech() {
  window.speechSynthesis?.cancel();
}

export function VoiceChatOverlay() {
  const isOpen = useVoiceChatStore((s) => s.isOpen);
  const setVoiceState = useVoiceChatStore((s) => s.setVoiceState);
  const setConnected = useVoiceChatStore((s) => s.setConnected);

  const addMessage = useConversationStore((s) => s.addMessage);
  const appendToLast = useConversationStore((s) => s.appendToLast);

  const [statusMsg, setStatusMsg] = useState<string | null>(null);
  const statusTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const isThinkingRef = useRef(false);
  const hasGreetedRef = useRef(false);
  const collectedTextRef = useRef("");
  const gotAudioResponseRef = useRef(false);
  const browserTtsFallbackTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const { playWithAnalysis, stopPlayback, cleanup: cleanupAudio } = useAudioPlayback();

  const showStatus = useCallback((msg: string, durationMs = 4000) => {
    setStatusMsg(msg);
    if (statusTimerRef.current) clearTimeout(statusTimerRef.current);
    statusTimerRef.current = setTimeout(() => setStatusMsg(null), durationMs);
  }, []);

  const handleWsMessage = useCallback(
    (data: Record<string, unknown>) => {
      const type = data.type as string;
      const content = (data.content as string) || "";

      switch (type) {
        case "thinking":
          isThinkingRef.current = true;
          setVoiceState("processing");
          break;

        case "text":
          collectedTextRef.current += content;
          if (isThinkingRef.current) {
            isThinkingRef.current = false;
            addMessage(AXON_CONVERSATION_ID, {
              id: `voice-ast-${Date.now()}`,
              role: "assistant",
              content,
              timestamp: Date.now(),
              metadata: { source: "voice" },
            });
          } else {
            appendToLast(AXON_CONVERSATION_ID, content);
          }
          break;

        case "transcription":
          if (content) {
            addMessage(AXON_CONVERSATION_ID, {
              id: `voice-user-${Date.now()}`,
              role: "user",
              content,
              timestamp: Date.now(),
              metadata: { source: "voice" },
            });
            setVoiceState("processing");
          }
          break;

        case "audio_response":
          if (data.audio) {
            gotAudioResponseRef.current = true;
            // Cancel browser TTS fallback if it was pending
            if (browserTtsFallbackTimerRef.current) {
              clearTimeout(browserTtsFallbackTimerRef.current);
              browserTtsFallbackTimerRef.current = null;
            }
            cancelBrowserSpeech();
            setVoiceState("speaking");
            playWithAnalysis(data.audio as string)
              .then(() => {
                // Reset for next turn
                gotAudioResponseRef.current = false;
                setVoiceState("idle");
              })
              .catch(() => {
                gotAudioResponseRef.current = false;
                setVoiceState("idle");
              });
          }
          break;

        case "done": {
          isThinkingRef.current = false;

          // audio_response arrives AFTER done (TTS synthesis takes time).
          // Wait before falling back to browser TTS.
          const pendingText = collectedTextRef.current.trim();
          collectedTextRef.current = "";

          if (!gotAudioResponseRef.current && pendingText) {
            // Keep processing state while waiting for TTS
            setVoiceState("processing");
            browserTtsFallbackTimerRef.current = setTimeout(() => {
              browserTtsFallbackTimerRef.current = null;
              if (!gotAudioResponseRef.current) {
                gotAudioResponseRef.current = false;
                setVoiceState("speaking");
                speakWithBrowser(pendingText).then(() => {
                  if (useVoiceChatStore.getState().voiceState === "speaking") {
                    setVoiceState("idle");
                  }
                });
              }
            }, 5000);
          } else if (!gotAudioResponseRef.current) {
            // No text collected and no audio — just go idle
            setVoiceState("idle");
          }
          // If gotAudioResponseRef is true, audio_response handler manages state
          break;
        }

        case "error":
          isThinkingRef.current = false;
          collectedTextRef.current = "";
          gotAudioResponseRef.current = false;
          showStatus(content || "Something went wrong");
          addMessage(AXON_CONVERSATION_ID, {
            id: `voice-err-${Date.now()}`,
            role: "system",
            content: `Error: ${content}`,
            timestamp: Date.now(),
            metadata: { source: "voice" },
          });
          setVoiceState("idle");
          break;
      }
    },
    [setVoiceState, addMessage, appendToLast, playWithAnalysis, showStatus]
  );

  const { connected, send, disconnect } = useWebSocket({
    url: "/api/conversations/ws/axon",
    onMessage: handleWsMessage,
    autoConnect: isOpen,
  });

  useEffect(() => {
    setConnected(connected);
  }, [connected, setConnected]);

  useEffect(() => {
    if (connected && isOpen && !hasGreetedRef.current) {
      hasGreetedRef.current = true;
      send({ type: "greeting" });
    }
  }, [connected, isOpen, send]);

  const onAudio = useCallback(
    (audioBase64: string, sampleRate: number, format: string) => {
      // Reset turn state for new audio segment
      gotAudioResponseRef.current = false;
      collectedTextRef.current = "";
      if (browserTtsFallbackTimerRef.current) {
        clearTimeout(browserTtsFallbackTimerRef.current);
        browserTtsFallbackTimerRef.current = null;
      }
      const voice = useVoiceChatStore.getState().selectedVoice;
      send({ type: "audio", audio: audioBase64, sample_rate: sampleRate, format, ...(voice && { voice_id: voice }) });
      setVoiceState("processing");
    },
    [send, setVoiceState]
  );

  const onSpeechStart = useCallback(() => {
    const state = useVoiceChatStore.getState();
    if (state.autoInterrupt && state.voiceState === "speaking") {
      stopPlayback();
      cancelBrowserSpeech();
    }
    setVoiceState("listening");
  }, [stopPlayback, setVoiceState]);

  const { supported: micSupported } = useVoiceContinuous({
    onAudio,
    enabled: isOpen && connected,
    onSpeechStart,
  });

  useEffect(() => {
    if (!isOpen) {
      stopPlayback();
      cancelBrowserSpeech();
      if (browserTtsFallbackTimerRef.current) {
        clearTimeout(browserTtsFallbackTimerRef.current);
        browserTtsFallbackTimerRef.current = null;
      }
      cleanupAudio();
      disconnect();
      hasGreetedRef.current = false;
      isThinkingRef.current = false;
      collectedTextRef.current = "";
      gotAudioResponseRef.current = false;
      setStatusMsg(null);
    }
  }, [isOpen, disconnect, stopPlayback, cleanupAudio]);

  return (
    <>
      <AnimatePresence>
        {isOpen && (
          <motion.div
            key="voice-overlay"
            initial={{ opacity: 0, scale: 0.95, y: 12 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 12 }}
            transition={{ duration: 0.3, ease: [0.25, 1, 0.5, 1] }}
            className={[
              "fixed z-50 flex flex-col items-center justify-center overflow-hidden",
              "inset-0 bg-base-100/95 backdrop-blur-sm",
              "md:inset-auto md:bottom-20 md:right-6 md:w-72 md:h-80 md:rounded-2xl md:bg-base-200 md:border md:border-neutral md:shadow-2xl md:backdrop-blur-none lg:w-80 lg:h-96",
            ].join(" ")}
          >
            {/* Orb — staggered entrance */}
            <motion.div
              className="flex-1 flex items-center justify-center"
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.4, delay: 0.1, ease: [0.25, 1, 0.5, 1] }}
            >
              <SparkleOrb />
            </motion.div>

            <AnimatePresence>
              {statusMsg && (
                <motion.div
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: 6 }}
                  transition={{ duration: 0.2, ease: [0.25, 1, 0.5, 1] }}
                  className="px-4 pb-2 text-center text-xs text-warning/80 max-w-full truncate"
                >
                  {statusMsg}
                </motion.div>
              )}
            </AnimatePresence>

            <AnimatePresence>
              {!micSupported && (
                <motion.div
                  initial={{ opacity: 0, y: 4 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: 4 }}
                  transition={{ duration: 0.2 }}
                  className="text-center text-xs text-error px-4 pb-2"
                >
                  Microphone not available
                </motion.div>
              )}
            </AnimatePresence>

            {/* Controls — staggered entrance */}
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3, delay: 0.2, ease: [0.25, 1, 0.5, 1] }}
            >
              <VoiceControls />
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
