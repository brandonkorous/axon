import { useVoiceChatStore } from "../../stores/voiceChatStore";

/** Must match vadThresholds() in useVoiceContinuous — threshold = 0.005 + s * 0.035 */
function speechThreshold(sensitivity: number): number {
  const s = Math.max(0, Math.min(1, sensitivity));
  return 0.005 + s * 0.035;
}

/** Max RMS the meter visualizes — values above are clamped. */
const METER_MAX = 0.08;

export function MicCalibration() {
  const sensitivity = useVoiceChatStore((s) => s.sensitivity);
  const setSensitivity = useVoiceChatStore((s) => s.setSensitivity);
  const amplitude = useVoiceChatStore((s) => s.amplitude);

  const threshold = speechThreshold(sensitivity);
  const levelPct = Math.min(100, (amplitude / METER_MAX) * 100);
  const thresholdPct = Math.min(100, (threshold / METER_MAX) * 100);

  return (
    <div className="space-y-3">
      <h4 className="text-xs font-semibold uppercase tracking-wider text-base-content/50">
        Microphone
      </h4>

      {/* Live level meter */}
      <div className="space-y-1">
        <div className="text-xs text-base-content/60">Audio level</div>
        <div className="relative h-2 bg-base-300 rounded-full overflow-hidden">
          {/* Amplitude fill */}
          <div
            className="absolute inset-y-0 left-0 rounded-full transition-[width] duration-[50ms] linear"
            style={{
              width: `${levelPct}%`,
              backgroundColor: levelPct > thresholdPct ? "oklch(var(--su))" : "oklch(var(--bc) / 0.25)",
            }}
          />
          {/* Threshold marker */}
          <div
            className="absolute inset-y-0 w-0.5 bg-warning"
            style={{ left: `${thresholdPct}%` }}
            title={`Trigger threshold: ${threshold.toFixed(3)}`}
          />
        </div>
        <div className="text-[10px] text-base-content/50 flex justify-between">
          <span>Quiet</span>
          <span className="text-warning/60">▲ trigger</span>
          <span>Loud</span>
        </div>
      </div>

      {/* Sensitivity slider */}
      <div className="space-y-1">
        <div className="text-xs text-base-content/60">Sensitivity</div>
        <input
          type="range"
          min={0}
          max={1}
          step={0.05}
          value={sensitivity}
          onChange={(e) => setSensitivity(parseFloat(e.target.value))}
          className="range range-xs range-primary w-full"
          aria-label="Microphone sensitivity"
        />
        <div className="text-[10px] text-base-content/50 flex justify-between">
          <span>More sensitive</span>
          <span>Less sensitive</span>
        </div>
      </div>
    </div>
  );
}
