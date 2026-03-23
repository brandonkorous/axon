import { useCallback, useEffect, useState } from "react";
import { useVoiceChatStore } from "../../stores/voiceChatStore";

interface VoiceEntry {
  key: string;
  name: string;
  language: string;
  language_name: string;
  country: string;
  quality: string;
  size_mb: number;
  installed: boolean;
}

export function VoiceSelector() {
  const selectedVoice = useVoiceChatStore((s) => s.selectedVoice);
  const setSelectedVoice = useVoiceChatStore((s) => s.setSelectedVoice);
  const settingsOpen = useVoiceChatStore((s) => s.settingsOpen);

  const [voices, setVoices] = useState<VoiceEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [downloading, setDownloading] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [fetched, setFetched] = useState(false);

  const fetchVoices = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await fetch("/api/voices");
      if (!res.ok) throw new Error(`${res.status}`);
      const data = await res.json();
      setVoices(data.voices ?? []);
      setFetched(true);
    } catch {
      setError("Could not load voice list");
    } finally {
      setLoading(false);
    }
  }, []);

  // Fetch only when the settings modal opens
  useEffect(() => {
    if (settingsOpen && !fetched) {
      fetchVoices();
    }
  }, [settingsOpen, fetched, fetchVoices]);

  const handleDownload = async (key: string) => {
    setDownloading(key);
    setError(null);
    try {
      const res = await fetch("/api/voices/download", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ voice_key: key }),
      });
      if (!res.ok) throw new Error("Download failed");
      await fetchVoices();
      setSelectedVoice(key);
    } catch {
      setError(`Failed to download ${key}`);
    } finally {
      setDownloading(null);
    }
  };

  const installed = voices.filter((v) => v.installed);
  const available = voices.filter((v) => !v.installed);

  return (
    <div className="space-y-3">
      <h4 className="text-xs font-semibold uppercase tracking-wider text-base-content/50">
        Voice
      </h4>

      {/* Dropdown — always show with at least "Agent default" */}
      <select
        className="select select-sm select-bordered w-full text-xs"
        value={selectedVoice}
        onChange={(e) => setSelectedVoice(e.target.value)}
        aria-label="Select voice"
      >
        <option value="">Agent default</option>
        {installed.map((v) => (
          <option key={v.key} value={v.key}>
            {formatVoiceName(v)}
          </option>
        ))}
      </select>

      {/* Loading state */}
      {loading && (
        <div className="text-xs text-base-content/40 flex items-center gap-2">
          <span className="loading loading-spinner loading-xs" />
          Loading voices from catalog...
        </div>
      )}

      {/* Error with retry */}
      {error && (
        <div className="flex items-center justify-between">
          <span className="text-[10px] text-error">{error}</span>
          <button
            className="btn btn-ghost btn-xs text-[10px]"
            onClick={fetchVoices}
            disabled={loading}
          >
            Retry
          </button>
        </div>
      )}

      {/* Available to download */}
      {available.length > 0 && (
        <details className="collapse collapse-arrow bg-base-300/50 rounded-lg">
          <summary className="collapse-title text-xs font-medium min-h-0 py-2 px-3">
            Download more voices ({available.length})
          </summary>
          <div className="collapse-content px-3 pb-2">
            <div className="max-h-48 overflow-y-auto space-y-1">
              {available.map((v) => (
                <div
                  key={v.key}
                  className="flex items-center justify-between gap-2 py-1"
                >
                  <div className="min-w-0">
                    <div className="text-xs truncate">{formatVoiceName(v)}</div>
                    <div className="text-[10px] text-base-content/40">
                      {v.quality} &middot; {v.size_mb} MB
                    </div>
                  </div>
                  <button
                    className="btn btn-ghost btn-xs flex-shrink-0"
                    onClick={() => handleDownload(v.key)}
                    disabled={downloading !== null}
                  >
                    {downloading === v.key ? (
                      <span className="loading loading-spinner loading-xs" />
                    ) : (
                      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} className="w-3.5 h-3.5">
                        <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M7 10l5 5 5-5M12 15V3" />
                      </svg>
                    )}
                  </button>
                </div>
              ))}
            </div>
          </div>
        </details>
      )}
    </div>
  );
}

function formatVoiceName(v: VoiceEntry): string {
  // "en_US-lessac-medium" → "Lessac (US, medium)"
  const parts = v.key.split("-");
  const name = parts[1] ? parts[1].charAt(0).toUpperCase() + parts[1].slice(1) : v.key;
  const quality = parts[2] || v.quality;
  // Prefer metadata, fall back to parsing country from key prefix (e.g. "en_US" → "US")
  const lang = v.country || v.language || (parts[0]?.split("_")[1] ?? "");
  const details = [lang, quality].filter(Boolean).join(", ");
  return details ? `${name} (${details})` : name;
}
