import { useState, useRef, useCallback, type KeyboardEvent } from "react";
import { useVoice } from "../../hooks/useVoice";
import { SLASH_COMMANDS } from "../../constants/slashCommands";
import { InputAutocomplete, type AutocompleteItem } from "./CommandAutocomplete";
import type { AgentInfo } from "../../stores/agentStore";

interface Props {
  onSend: (message: string) => void;
  onCommand?: (name: string, args: string) => void;
  onAudio?: (audioBase64: string, sampleRate: number, format: string) => void;
  agents?: AgentInfo[];
  placeholder?: string;
  disabled?: boolean;
}

export function ChatInput({
  onSend,
  onCommand,
  onAudio,
  agents = [],
  placeholder = "Message Axon...",
  disabled = false,
}: Props) {
  const [input, setInput] = useState("");
  const [acItems, setAcItems] = useState<AutocompleteItem[]>([]);
  const [acMode, setAcMode] = useState<"command" | "mention" | null>(null);
  const [selectedIndex, setSelectedIndex] = useState(0);
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

    if (trimmed.startsWith("/") && onCommand) {
      const spaceIdx = trimmed.indexOf(" ");
      const name = spaceIdx > 0 ? trimmed.slice(1, spaceIdx) : trimmed.slice(1);
      const args = spaceIdx > 0 ? trimmed.slice(spaceIdx + 1).trim() : "";
      onCommand(name, args);
    } else {
      onSend(trimmed);
    }
    setInput("");
    closeAutocomplete();
    inputRef.current?.focus();
  };

  const closeAutocomplete = () => {
    setAcItems([]);
    setAcMode(null);
  };

  const handleInputChange = (val: string) => {
    setInput(val);

    // Slash commands: trigger on "/" at start, before any space
    if (val.startsWith("/") && !val.includes(" ")) {
      const prefix = val.slice(1).toLowerCase();
      const items: AutocompleteItem[] = SLASH_COMMANDS
        .filter((c) => c.name.startsWith(prefix))
        .map((c) => ({
          key: c.name,
          label: `/${c.name}`,
          detail: c.description,
          hint: c.argHint,
        }));
      if (items.length > 0) {
        setAcItems(items);
        setAcMode("command");
        setSelectedIndex(0);
        return;
      }
    }

    // @mentions: trigger on "@" at start, before any space
    if (val.startsWith("@") && !val.includes(" ")) {
      const prefix = val.slice(1).toLowerCase();
      const items: AutocompleteItem[] = agents
        .filter((a) => a.id.startsWith(prefix) || a.name.toLowerCase().startsWith(prefix))
        .map((a) => ({
          key: a.id,
          label: `@${a.name.toLowerCase()}`,
          detail: a.title,
          color: a.ui.color,
        }));
      if (items.length > 0) {
        setAcItems(items);
        setAcMode("mention");
        setSelectedIndex(0);
        return;
      }
    }

    closeAutocomplete();
  };

  const selectItem = (item: AutocompleteItem) => {
    if (acMode === "command") {
      const cmd = SLASH_COMMANDS.find((c) => c.name === item.key);
      const suffix = cmd?.hasArgs ? " " : "";
      setInput(`/${item.key}${suffix}`);
    } else if (acMode === "mention") {
      setInput(`@${item.key} `);
    }
    closeAutocomplete();
    inputRef.current?.focus();
  };

  const handleKeyDown = (e: KeyboardEvent) => {
    if (acMode) {
      if (e.key === "ArrowDown") {
        e.preventDefault();
        setSelectedIndex((i) => Math.min(i + 1, acItems.length - 1));
        return;
      }
      if (e.key === "ArrowUp") {
        e.preventDefault();
        setSelectedIndex((i) => Math.max(i - 1, 0));
        return;
      }
      if (e.key === "Tab") {
        e.preventDefault();
        const item = acItems[selectedIndex];
        if (item) selectItem(item);
        return;
      }
      if (e.key === "Escape") {
        closeAutocomplete();
        return;
      }
    }
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="bg-base-200 p-4">
      <div className="relative flex gap-2 items-end max-w-4xl mx-auto">
        {acMode && (
          <InputAutocomplete
            items={acItems}
            selectedIndex={selectedIndex}
            onSelect={selectItem}
          />
        )}

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
          onChange={(e) => handleInputChange(e.target.value)}
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
