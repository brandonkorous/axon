import { useState, useRef, useCallback, type KeyboardEvent } from "react";
import { useVoice } from "../../hooks/useVoice";

interface Props {
  onSend: (message: string) => void;
  onAudio?: (audioBase64: string, sampleRate: number, format: string) => void;
  placeholder?: string;
  disabled?: boolean;
}

export function ChatInput({
  onSend,
  onAudio,
  placeholder = "Message Axon...",
  disabled = false,
}: Props) {
  const [input, setInput] = useState("");
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const handleAudio = useCallback(
    (audio: string, sr: number, format: string) => {
      if (onAudio) onAudio(audio, sr, format);
    },
    [onAudio]
  );

  const { recording, processing, supported: micSupported, toggleRecording } = useVoice({
    onAudio: handleAudio,
  });

  const handleSend = () => {
    const trimmed = input.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setInput("");
    inputRef.current?.focus();
  };

  const handleKeyDown = (e: KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="border-t border-neutral bg-base-200 p-4">
      <div className="flex gap-2 items-end max-w-4xl mx-auto">
        {micSupported && onAudio && (
          <button
            onClick={toggleRecording}
            disabled={disabled || processing}
            aria-label={recording ? "Stop recording" : processing ? "Processing audio" : "Start voice input"}
            className={`btn btn-square shrink-0 ${
              recording
                ? "btn-error animate-pulse"
                : processing
                  ? "btn-primary"
                  : "btn-ghost border-secondary"
            }`}
          >
            {processing ? (
              <span className="loading loading-spinner loading-sm" />
            ) : (
              <svg
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth={2}
                strokeLinecap="round"
                strokeLinejoin="round"
                className="w-5 h-5"
              >
                {recording ? (
                  <rect x="6" y="6" width="12" height="12" rx="2" fill="currentColor" />
                ) : (
                  <>
                    <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" />
                    <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
                    <line x1="12" y1="19" x2="12" y2="23" />
                    <line x1="8" y1="23" x2="16" y2="23" />
                  </>
                )}
              </svg>
            )}
          </button>
        )}

        <textarea
          ref={inputRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={recording ? "Listening..." : processing ? "Processing audio..." : placeholder}
          disabled={disabled || recording || processing}
          rows={1}
          aria-label="Message input"
          className="textarea flex-1 resize-none"
          style={{ minHeight: "44px", maxHeight: "200px" }}
          onInput={(e) => {
            const target = e.target as HTMLTextAreaElement;
            target.style.height = "auto";
            target.style.height = `${Math.min(target.scrollHeight, 200)}px`;
          }}
        />
        <button
          onClick={handleSend}
          disabled={!input.trim() || disabled}
          className="btn btn-primary"
        >
          Send
        </button>
      </div>
    </div>
  );
}
