import { useCallback, useEffect, useRef, useState } from "react";
import { useVoiceChatStore } from "../stores/voiceChatStore";

/**
 * Sensitivity-scaled VAD thresholds.
 * sensitivity 0 (most sensitive): threshold 0.005, 2 frames
 * sensitivity 0.5 (default):      threshold 0.015, 3 frames
 * sensitivity 1 (least sensitive): threshold 0.04,  5 frames
 */
function vadThresholds(sensitivity: number) {
  const s = Math.max(0, Math.min(1, sensitivity));
  return {
    speechThreshold: 0.005 + s * 0.035,
    speechMinFrames: Math.round(2 + s * 3),
  };
}

interface UseVoiceContinuousOptions {
  /** Called with base64-encoded audio when a speech segment ends (silence detected). */
  onAudio: (audioBase64: string, sampleRate: number, format: string) => void;
  /** Whether the mic should be open and VAD active. */
  enabled: boolean;
  /** Fires when VAD detects the user started speaking. */
  onSpeechStart?: () => void;
  /** Fires after the recording segment is finalized and sent. */
  onSpeechEnd?: () => void;
}

/**
 * Continuous voice hook with Voice Activity Detection.
 *
 * Opens the mic once and keeps it open. A requestAnimationFrame loop
 * monitors RMS amplitude. When speech is detected, a MediaRecorder
 * starts capturing. When silence persists for SILENCE_TIMEOUT ms,
 * the recording is stopped and the audio blob is sent via onAudio.
 *
 * Also writes mic amplitude to voiceChatStore so the orb reacts
 * to the user's voice in real time.
 */
export function useVoiceContinuous({
  onAudio,
  enabled,
  onSpeechStart,
  onSpeechEnd,
}: UseVoiceContinuousOptions) {
  const [supported] = useState(
    typeof navigator !== "undefined" && !!navigator.mediaDevices?.getUserMedia
  );
  const [speaking, setSpeaking] = useState(false);

  const streamRef = useRef<MediaStream | null>(null);
  const audioCtxRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const rafRef = useRef<number>(0);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  const speechFrameCountRef = useRef(0);
  const silenceStartRef = useRef(0);
  const isRecordingRef = useRef(false);

  // Stable refs for values needed inside the RAF loop
  const enabledRef = useRef(enabled);
  const onAudioRef = useRef(onAudio);
  const onSpeechStartRef = useRef(onSpeechStart);
  const onSpeechEndRef = useRef(onSpeechEnd);
  enabledRef.current = enabled;
  onAudioRef.current = onAudio;
  onSpeechStartRef.current = onSpeechStart;
  onSpeechEndRef.current = onSpeechEnd;

  // --- Recording segment helpers ---

  const stopCurrentRecording = useCallback(() => {
    if (mediaRecorderRef.current?.state === "recording") {
      mediaRecorderRef.current.stop();
    }
    isRecordingRef.current = false;
    setSpeaking(false);
  }, []);

  const startRecordingSegment = useCallback(() => {
    const stream = streamRef.current;
    if (!stream || isRecordingRef.current) return;

    const mimeType = MediaRecorder.isTypeSupported("audio/webm;codecs=opus")
      ? "audio/webm;codecs=opus"
      : "audio/webm";

    const recorder = new MediaRecorder(stream, { mimeType });
    chunksRef.current = [];

    recorder.ondataavailable = (e) => {
      if (e.data.size > 0) chunksRef.current.push(e.data);
    };

    recorder.onstop = async () => {
      if (chunksRef.current.length === 0) return;
      try {
        const blob = new Blob(chunksRef.current, { type: mimeType });
        const arrayBuffer = await blob.arrayBuffer();
        const bytes = new Uint8Array(arrayBuffer);
        let binary = "";
        for (let i = 0; i < bytes.length; i++) {
          binary += String.fromCharCode(bytes[i]);
        }
        const base64 = btoa(binary);
        const format = mimeType.includes("opus") ? "webm/opus" : "webm";
        console.log("[VAD] Sending audio segment:", Math.round(blob.size / 1024), "KB");
        onAudioRef.current(base64, 48000, format);
      } catch (err) {
        console.error("[VAD] Failed to process audio segment:", err);
      }
      onSpeechEndRef.current?.();
    };

    mediaRecorderRef.current = recorder;
    recorder.start(100);
    isRecordingRef.current = true;
    setSpeaking(true);
    console.log("[VAD] Speech detected — recording started");
    onSpeechStartRef.current?.();
  }, []);

  // --- VAD loop ---

  const startVAD = useCallback(() => {
    const analyser = analyserRef.current;
    if (!analyser) {
      console.warn("[VAD] No analyser — cannot start VAD");
      return;
    }

    const data = new Uint8Array(analyser.frequencyBinCount);
    let logCountdown = 0; // throttle debug logs

    console.log("[VAD] Started monitoring mic input");

    const tick = () => {
      if (!enabledRef.current) {
        // Keep the loop alive but skip processing
        rafRef.current = requestAnimationFrame(tick);
        return;
      }

      analyser.getByteTimeDomainData(data);

      let sum = 0;
      for (let i = 0; i < data.length; i++) {
        const sample = (data[i] - 128) / 128;
        sum += sample * sample;
      }
      const rms = Math.sqrt(sum / data.length);

      // Read current settings and compute thresholds
      const store = useVoiceChatStore.getState();
      const { speechThreshold, speechMinFrames } = vadThresholds(store.sensitivity);
      const silenceTimeout = store.silenceTimeout;

      // Write mic amplitude to store so the orb reacts to user's voice
      if (store.voiceState !== "speaking") {
        store.setAmplitude(Math.min(1, rms * 2.5));
      }

      // Periodic debug log
      if (logCountdown <= 0 && rms > 0.005) {
        console.log("[VAD] RMS:", rms.toFixed(4), "threshold:", speechThreshold.toFixed(4), "recording:", isRecordingRef.current);
        logCountdown = 60; // ~1 second between logs at 60fps
      }
      logCountdown--;

      const isSpeech = rms > speechThreshold && !store.muted;

      if (isSpeech) {
        speechFrameCountRef.current++;
        silenceStartRef.current = 0;

        // Start recording after enough consecutive speech frames
        // Skip recording when settings modal is open (mic stays live for level meter)
        if (
          speechFrameCountRef.current >= speechMinFrames &&
          !isRecordingRef.current &&
          !store.settingsOpen
        ) {
          startRecordingSegment();
        }
      } else {
        speechFrameCountRef.current = 0;

        // If currently recording, track silence duration
        if (isRecordingRef.current) {
          if (silenceStartRef.current === 0) {
            silenceStartRef.current = performance.now();
          } else if (
            performance.now() - silenceStartRef.current >
            silenceTimeout
          ) {
            console.log("[VAD] Silence detected — stopping recording");
            stopCurrentRecording();
            silenceStartRef.current = 0;
          }
        }
      }

      rafRef.current = requestAnimationFrame(tick);
    };

    rafRef.current = requestAnimationFrame(tick);
  }, [startRecordingSegment, stopCurrentRecording]);

  // --- Lifecycle: open/close mic stream ---

  useEffect(() => {
    if (!supported || !enabled) {
      // Teardown
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
      rafRef.current = 0;
      stopCurrentRecording();
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((t) => t.stop());
        streamRef.current = null;
      }
      if (audioCtxRef.current && audioCtxRef.current.state !== "closed") {
        audioCtxRef.current.close().catch(() => {});
        audioCtxRef.current = null;
      }
      analyserRef.current = null;
      speechFrameCountRef.current = 0;
      silenceStartRef.current = 0;
      useVoiceChatStore.getState().setAmplitude(0);
      return;
    }

    let cancelled = false;

    (async () => {
      try {
        console.log("[VAD] Requesting mic access...");
        const stream = await navigator.mediaDevices.getUserMedia({
          audio: {
            channelCount: 1,
            echoCancellation: true,
            noiseSuppression: true,
            autoGainControl: true,
          },
        });

        if (cancelled) {
          stream.getTracks().forEach((t) => t.stop());
          return;
        }

        console.log("[VAD] Mic stream acquired");
        streamRef.current = stream;

        const ctx = new AudioContext();
        // Ensure AudioContext is running (browsers may start it suspended)
        if (ctx.state === "suspended") {
          await ctx.resume();
        }
        console.log("[VAD] AudioContext state:", ctx.state);
        audioCtxRef.current = ctx;

        const source = ctx.createMediaStreamSource(stream);
        const analyser = ctx.createAnalyser();
        analyser.fftSize = 512;
        analyser.smoothingTimeConstant = 0.3;
        source.connect(analyser);
        analyserRef.current = analyser;

        startVAD();
      } catch (err) {
        console.error("[VAD] Mic access denied:", err);
      }
    })();

    return () => {
      cancelled = true;
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
      rafRef.current = 0;
      stopCurrentRecording();
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((t) => t.stop());
        streamRef.current = null;
      }
      if (audioCtxRef.current && audioCtxRef.current.state !== "closed") {
        audioCtxRef.current.close().catch(() => {});
        audioCtxRef.current = null;
      }
    };
  }, [enabled, supported, startVAD, stopCurrentRecording]);

  return { speaking, supported };
}
