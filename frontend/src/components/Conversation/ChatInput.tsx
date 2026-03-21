import { useState, useRef, type KeyboardEvent } from "react";

interface Props {
  onSend: (message: string) => void;
  placeholder?: string;
  disabled?: boolean;
}

export function ChatInput({
  onSend,
  placeholder = "Message Axon...",
  disabled = false,
}: Props) {
  const [input, setInput] = useState("");
  const inputRef = useRef<HTMLTextAreaElement>(null);

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
    <div className="border-t border-gray-800 bg-gray-900 p-4">
      <div className="flex gap-2 items-end max-w-4xl mx-auto">
        <textarea
          ref={inputRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={disabled}
          rows={1}
          className="flex-1 bg-gray-800 border border-gray-700 rounded-xl px-4 py-3 text-gray-100 placeholder-gray-500 resize-none focus:outline-none focus:ring-2 focus:ring-violet-500/50 focus:border-violet-500/50 disabled:opacity-50"
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
          className="bg-violet-600 hover:bg-violet-500 disabled:bg-gray-700 disabled:text-gray-500 text-white rounded-xl px-4 py-3 font-medium transition-colors"
        >
          Send
        </button>
      </div>
    </div>
  );
}
