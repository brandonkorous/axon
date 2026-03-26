import { memo, useEffect, useMemo } from "react";
import {
  motion,
  AnimatePresence,
  useMotionValue,
  useReducedMotion,
  useTransform,
} from "framer-motion";
import { useVoiceChatStore, VoiceState } from "../../stores/voiceChatStore";
import { useAgentStore } from "../../stores/agentStore";
import { DEFAULT_AGENT_COLOR } from "../../constants/theme";

const ORB_SIZE = 80;

function useOrbColor() {
  const agents = useAgentStore((s) => s.agents);
  const axon = agents.find((a) => a.id === "axon");
  return axon?.ui?.sparkle_color || axon?.ui?.color || DEFAULT_AGENT_COLOR;
}

const CoreOrb = memo(function CoreOrb({ voiceState, color }: { voiceState: VoiceState; color: string }) {
  const amplitude = useVoiceChatStore((s) => s.amplitude);
  const scale = useMotionValue(1);

  useEffect(() => {
    if (voiceState === "speaking") {
      scale.set(1 + amplitude * 0.3);
    }
  }, [voiceState, amplitude, scale]);

  const shadowSpread = useTransform(scale, [1, 1.3], [0, 30]);
  const boxShadow = useTransform(
    shadowSpread,
    (s) => `0 0 ${s}px ${s * 0.6}px ${color}66`
  );

  const variants = {
    idle: {
      scale: [1, 1.05, 1],
      transition: { duration: 3, repeat: Infinity, ease: "easeInOut" as const },
    },
    listening: {
      scale: [1, 1.12, 1],
      transition: { duration: 1.2, repeat: Infinity, ease: "easeInOut" as const },
    },
    processing: {
      scale: [1, 0.92, 1.08, 1],
      rotate: 360,
      transition: {
        scale: { duration: 2, repeat: Infinity, ease: "easeInOut" as const },
        rotate: { duration: 3, repeat: Infinity, ease: "linear" as const },
      },
    },
    speaking: {},
  };

  return (
    <motion.div
      variants={variants}
      animate={voiceState === "speaking" ? undefined : voiceState}
      style={{
        width: ORB_SIZE,
        height: ORB_SIZE,
        borderRadius: "50%",
        background: `radial-gradient(circle at 35% 35%, ${color}, ${color}88 60%, ${color}44)`,
        boxShadow: voiceState === "speaking" ? boxShadow : `0 0 20px 4px ${color}44`,
        scale: voiceState === "speaking" ? scale : undefined,
        willChange: "transform, box-shadow",
      }}
    />
  );
});

const RippleRings = memo(function RippleRings({ color }: { color: string }) {
  return (
    <>
      {[0, 0.6, 1.2].map((delay) => (
        <motion.div
          key={delay}
          initial={{ scale: 0.5, opacity: 0.4 }}
          animate={{ scale: 2.5, opacity: 0 }}
          transition={{ duration: 2, repeat: Infinity, delay, ease: "easeOut" }}
          style={{
            position: "absolute",
            width: ORB_SIZE,
            height: ORB_SIZE,
            borderRadius: "50%",
            border: `2px solid ${color}55`,
            willChange: "transform, opacity",
          }}
        />
      ))}
    </>
  );
});

const OrbitingDots = memo(function OrbitingDots({ color }: { color: string }) {
  const dots = useMemo(
    () =>
      [1.5, 2, 2.5, 3].map((dur, i) => ({
        duration: dur,
        offset: (i * 360) / 4,
        size: 6 - i,
      })),
    []
  );

  return (
    <>
      {dots.map((dot, i) => (
        <motion.div
          key={i}
          animate={{ rotate: 360 }}
          transition={{ duration: dot.duration, repeat: Infinity, ease: "linear" }}
          style={{
            position: "absolute",
            width: ORB_SIZE * 2,
            height: ORB_SIZE * 2,
          }}
        >
          <div
            style={{
              position: "absolute",
              top: 0,
              left: "50%",
              transform: `translateX(-50%) rotate(${dot.offset}deg)`,
              width: dot.size,
              height: dot.size,
              borderRadius: "50%",
              backgroundColor: color,
              opacity: 0.8,
            }}
          />
        </motion.div>
      ))}
    </>
  );
});

const GLOW_BASE_SIZE = 110;

const GlowRing = memo(function GlowRing({ voiceState, color }: { voiceState: VoiceState; color: string }) {
  const amplitude = useVoiceChatStore((s) => s.amplitude);

  const glowScale = voiceState === "speaking" ? (120 + amplitude * 40) / GLOW_BASE_SIZE : 1;
  const glowOpacity =
    voiceState === "speaking"
      ? 0.15 + amplitude * 0.35
      : voiceState === "listening"
        ? 0.25
        : 0.1;

  return (
    <motion.div
      animate={{ scale: glowScale, opacity: glowOpacity }}
      transition={{ duration: 0.1, ease: "easeOut" }}
      style={{
        position: "absolute",
        width: GLOW_BASE_SIZE,
        height: GLOW_BASE_SIZE,
        borderRadius: "50%",
        background: `radial-gradient(circle, ${color}44, transparent 70%)`,
        filter: "blur(8px)",
        willChange: "transform, opacity",
      }}
    />
  );
});

export function SparkleOrb() {
  const voiceState = useVoiceChatStore((s) => s.voiceState);
  const muted = useVoiceChatStore((s) => s.muted);
  const connected = useVoiceChatStore((s) => s.connected);
  const color = useOrbColor();
  const reduceMotion = useReducedMotion();

  const label = muted
    ? "Muted"
    : !connected
      ? "Connecting..."
      : voiceState === "idle"
        ? "Listening..."
        : voiceState === "listening"
          ? "Hearing you..."
          : voiceState === "processing"
            ? "Thinking..."
            : "Speaking...";

  return (
    <motion.div
      className="relative flex items-center justify-center w-40 h-40"
      role="status"
      aria-label={label}
      animate={{ opacity: muted ? 0.4 : 1, filter: muted ? "saturate(0.3)" : "saturate(1)" }}
      transition={{ duration: 0.4, ease: [0.25, 1, 0.5, 1] }}
    >
      {!reduceMotion && <GlowRing voiceState={voiceState} color={color} />}

      {!reduceMotion && (
        <AnimatePresence>
          {voiceState === "listening" && !muted && (
            <motion.div
              key="ripples"
              className="absolute flex items-center justify-center"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
            >
              <RippleRings color={color} />
            </motion.div>
          )}
        </AnimatePresence>
      )}

      {!reduceMotion && (
        <AnimatePresence>
          {voiceState === "processing" && (
            <motion.div
              key="orbits"
              className="absolute flex items-center justify-center"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
            >
              <OrbitingDots color={color} />
            </motion.div>
          )}
        </AnimatePresence>
      )}

      {reduceMotion ? (
        <div
          style={{
            width: ORB_SIZE,
            height: ORB_SIZE,
            borderRadius: "50%",
            background: color,
          }}
        />
      ) : (
        <CoreOrb voiceState={voiceState} color={color} />
      )}

      <motion.p
        className="absolute -bottom-6 text-xs text-base-content/60 whitespace-nowrap"
        key={label}
        initial={{ opacity: 0, y: 4 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
      >
        {label}
      </motion.p>
    </motion.div>
  );
}
