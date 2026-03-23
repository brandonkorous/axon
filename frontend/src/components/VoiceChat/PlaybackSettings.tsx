import { useVoiceChatStore } from "../../stores/voiceChatStore";

export function PlaybackSettings() {
  const silenceTimeout = useVoiceChatStore((s) => s.silenceTimeout);
  const setSilenceTimeout = useVoiceChatStore((s) => s.setSilenceTimeout);
  const playbackSpeed = useVoiceChatStore((s) => s.playbackSpeed);
  const setPlaybackSpeed = useVoiceChatStore((s) => s.setPlaybackSpeed);
  const autoInterrupt = useVoiceChatStore((s) => s.autoInterrupt);
  const setAutoInterrupt = useVoiceChatStore((s) => s.setAutoInterrupt);

  return (
    <div className="space-y-4">
      <h4 className="text-xs font-semibold uppercase tracking-wider text-base-content/50">
        Playback
      </h4>

      {/* Playback speed */}
      <div className="space-y-1">
        <div className="flex justify-between text-xs text-base-content/60">
          <span>Speed</span>
          <span className="tabular-nums font-medium text-base-content/80">
            {playbackSpeed.toFixed(1)}x
          </span>
        </div>
        <input
          type="range"
          min={0.5}
          max={2}
          step={0.1}
          value={playbackSpeed}
          onChange={(e) => setPlaybackSpeed(parseFloat(e.target.value))}
          className="range range-xs range-primary w-full"
          aria-label="Playback speed"
        />
        <div className="text-[10px] text-base-content/40 flex justify-between">
          <span>0.5x</span>
          <span>2.0x</span>
        </div>
      </div>

      {/* Silence timeout */}
      <div className="space-y-1">
        <div className="flex justify-between text-xs text-base-content/60">
          <span>Pause before send</span>
          <span className="tabular-nums font-medium text-base-content/80">
            {(silenceTimeout / 1000).toFixed(1)}s
          </span>
        </div>
        <input
          type="range"
          min={500}
          max={4000}
          step={100}
          value={silenceTimeout}
          onChange={(e) => setSilenceTimeout(parseFloat(e.target.value))}
          className="range range-xs range-primary w-full"
          aria-label="Silence timeout"
        />
        <div className="text-[10px] text-base-content/40 flex justify-between">
          <span>Quick (0.5s)</span>
          <span>Patient (4s)</span>
        </div>
      </div>

      {/* Auto-interrupt toggle */}
      <label className="flex items-center justify-between cursor-pointer">
        <span className="text-xs text-base-content/60">
          Interrupt AI when you speak
        </span>
        <input
          type="checkbox"
          className="toggle toggle-sm toggle-primary"
          checked={autoInterrupt}
          onChange={(e) => setAutoInterrupt(e.target.checked)}
        />
      </label>
    </div>
  );
}
