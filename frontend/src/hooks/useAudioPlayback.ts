import { useCallback, useRef } from "react";
import { useVoiceChatStore } from "../stores/voiceChatStore";

/**
 * Plays TTS audio through AudioContext → AnalyserNode → destination
 * so we can read frequency data and drive the sparkle orb visualization.
 */
export function useAudioPlayback() {
  const audioCtxRef = useRef<AudioContext | null>(null);
  const sourceRef = useRef<AudioBufferSourceNode | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const rafRef = useRef<number>(0);

  const getAudioContext = useCallback(() => {
    if (!audioCtxRef.current || audioCtxRef.current.state === "closed") {
      audioCtxRef.current = new AudioContext();
    }
    if (audioCtxRef.current.state === "suspended") {
      audioCtxRef.current.resume();
    }
    return audioCtxRef.current;
  }, []);

  const stopAmplitudeLoop = useCallback(() => {
    if (rafRef.current) {
      cancelAnimationFrame(rafRef.current);
      rafRef.current = 0;
    }
    useVoiceChatStore.getState().setAmplitude(0);
  }, []);

  const startAmplitudeLoop = useCallback(() => {
    const analyser = analyserRef.current;
    if (!analyser) return;

    const data = new Uint8Array(analyser.frequencyBinCount);

    const tick = () => {
      analyser.getByteTimeDomainData(data);

      // Compute RMS amplitude normalized to 0–1
      let sum = 0;
      for (let i = 0; i < data.length; i++) {
        const sample = (data[i] - 128) / 128;
        sum += sample * sample;
      }
      const rms = Math.sqrt(sum / data.length);
      useVoiceChatStore.getState().setAmplitude(Math.min(1, rms * 2.5));

      rafRef.current = requestAnimationFrame(tick);
    };

    rafRef.current = requestAnimationFrame(tick);
  }, []);

  const playWithAnalysis = useCallback(
    (base64Wav: string): Promise<void> => {
      return new Promise((resolve, reject) => {
        try {
          // Decode base64 to ArrayBuffer
          const binary = atob(base64Wav);
          const bytes = new Uint8Array(binary.length);
          for (let i = 0; i < binary.length; i++) {
            bytes[i] = binary.charCodeAt(i);
          }

          const ctx = getAudioContext();

          // Create analyser
          const analyser = ctx.createAnalyser();
          analyser.fftSize = 256;
          analyser.smoothingTimeConstant = 0.8;
          analyserRef.current = analyser;

          ctx.decodeAudioData(
            bytes.buffer.slice(0),
            (audioBuffer) => {
              // Stop any previous source
              if (sourceRef.current) {
                try {
                  sourceRef.current.stop();
                } catch {
                  /* already stopped */
                }
              }

              const source = ctx.createBufferSource();
              source.buffer = audioBuffer;
              source.connect(analyser);
              analyser.connect(ctx.destination);
              sourceRef.current = source;

              source.onended = () => {
                stopAmplitudeLoop();
                sourceRef.current = null;
                resolve();
              };

              source.playbackRate.value = useVoiceChatStore.getState().playbackSpeed;
              startAmplitudeLoop();
              source.start(0);
            },
            (err) => {
              stopAmplitudeLoop();
              reject(err);
            }
          );
        } catch (err) {
          stopAmplitudeLoop();
          reject(err);
        }
      });
    },
    [getAudioContext, startAmplitudeLoop, stopAmplitudeLoop]
  );

  const stopPlayback = useCallback(() => {
    stopAmplitudeLoop();
    if (sourceRef.current) {
      try {
        sourceRef.current.stop();
      } catch {
        /* already stopped */
      }
      sourceRef.current = null;
    }
  }, [stopAmplitudeLoop]);

  const cleanup = useCallback(() => {
    stopPlayback();
    if (audioCtxRef.current && audioCtxRef.current.state !== "closed") {
      audioCtxRef.current.close().catch(() => {});
      audioCtxRef.current = null;
    }
  }, [stopPlayback]);

  return { playWithAnalysis, stopPlayback, cleanup };
}
