import { useCallback, useEffect, useRef, useState } from "react";
import { ChatMessage } from "../Conversation/ChatMessage";
import { ChatInput } from "../Conversation/ChatInput";
import { ThinkingIndicator } from "../Sparkle/ThinkingIndicator";
import { useConversationStore } from "../../stores/conversationStore";
import { useWebSocket } from "../../hooks/useWebSocket";

const SPEAKER_COLORS: Record<string, string> = {
  marcus: "#EF4444",
  raj: "#3B82F6",
  diana: "#10B981",
  table: "#F59E0B",
};

const MODES = [
  { id: "standard", label: "Standard" },
  { id: "vote", label: "Vote" },
  { id: "devils_advocate", label: "Devil's Advocate" },
  { id: "pressure_test", label: "Pressure Test" },
  { id: "quick_take", label: "Quick Take" },
  { id: "decision", label: "Decision" },
];

const CONVERSATION_ID = "boardroom";

export function BoardroomView() {
  const { messages, addMessage, appendToLast } = useConversationStore();
  const [isThinking, setIsThinking] = useState(false);
  const [mode, setMode] = useState("standard");
  const [currentSpeaker, setCurrentSpeaker] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const conversationMessages = messages[CONVERSATION_ID] || [];

  const handleWsMessage = useCallback(
    (data: Record<string, unknown>) => {
      const type = data.type as string;
      const speaker = data.speaker as string | null;
      const target = data.target as string | null;
      const content = (data.content as string) || "";

      switch (type) {
        case "thinking":
          setIsThinking(true);
          break;
        case "text":
          if (isThinking || speaker !== currentSpeaker) {
            // New speaker or first chunk — create new message
            setIsThinking(false);
            setCurrentSpeaker(speaker);
            addMessage(CONVERSATION_ID, {
              id: `msg-${Date.now()}-${Math.random()}`,
              role: "assistant",
              content,
              agentId: speaker || undefined,
              speaker: speaker || undefined,
              target: target || undefined,
              timestamp: Date.now(),
            });
          } else {
            appendToLast(CONVERSATION_ID, content);
          }
          break;
        case "done":
          setIsThinking(false);
          setCurrentSpeaker(null);
          break;
      }
    },
    [addMessage, appendToLast, isThinking, currentSpeaker]
  );

  const { connected, send } = useWebSocket({
    url: "/api/boardroom/ws",
    onMessage: handleWsMessage,
  });

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [conversationMessages.length, isThinking]);

  const handleSend = (content: string) => {
    addMessage(CONVERSATION_ID, {
      id: `user-${Date.now()}`,
      role: "user",
      content,
      timestamp: Date.now(),
    });
    send({ type: "message", content, mode });
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="border-b border-gray-800 bg-gray-900 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-amber-500 flex items-center justify-center text-sm font-bold text-white">
              B
            </div>
            <div>
              <h2 className="text-lg font-semibold text-white">The Boardroom</h2>
              <p className="text-xs text-gray-500">Marcus, Raj, Diana</p>
            </div>
          </div>

          {/* Mode selector */}
          <div className="flex gap-1">
            {MODES.map((m) => (
              <button
                key={m.id}
                onClick={() => setMode(m.id)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                  mode === m.id
                    ? "bg-amber-500/20 text-amber-400 border border-amber-500/30"
                    : "text-gray-400 hover:text-white hover:bg-gray-800"
                }`}
              >
                {m.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {conversationMessages.map((msg) => (
          <ChatMessage key={msg.id} message={msg} />
        ))}
        {isThinking && (
          <ThinkingIndicator color="#F59E0B" agentName="Boardroom" />
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <ChatInput
        onSend={handleSend}
        placeholder="What should we discuss?"
        disabled={!connected}
      />
    </div>
  );
}
