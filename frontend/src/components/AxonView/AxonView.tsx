import { useCallback, useEffect, useRef, useState } from "react";
import { ChatMessage } from "../Conversation/ChatMessage";
import { ChatInput } from "../Conversation/ChatInput";
import { ThinkingIndicator } from "../Sparkle/ThinkingIndicator";
import { useConversationStore, type ChatMessage as ChatMessageType } from "../../stores/conversationStore";
import { useAgentStore } from "../../stores/agentStore";
import { useWebSocket } from "../../hooks/useWebSocket";

const CONVERSATION_ID = "axon";

export function AxonView() {
  const { messages, addMessage, appendToLast, clearMessages } = useConversationStore();
  const { agents, setAgentStatus } = useAgentStore();
  const [isThinking, setIsThinking] = useState(false);
  const [activeAgent, setActiveAgent] = useState<string>("axon");
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const hasGreetedRef = useRef(false);

  const conversationMessages = messages[CONVERSATION_ID] || [];

  const handleWsMessage = useCallback(
    (data: Record<string, unknown>) => {
      const type = data.type as string;
      const agentId = (data.agent_id as string) || "axon";
      const content = (data.content as string) || "";

      switch (type) {
        case "thinking":
          setIsThinking(true);
          setActiveAgent(agentId);
          setAgentStatus(agentId, "thinking");
          break;

        case "text":
          if (isThinking) {
            // First text chunk — create the message
            setIsThinking(false);
            addMessage(CONVERSATION_ID, {
              id: `msg-${Date.now()}`,
              role: "assistant",
              content,
              agentId,
              timestamp: Date.now(),
            });
          } else {
            appendToLast(CONVERSATION_ID, content);
          }
          break;

        case "route":
          // Axon is routing to another agent
          const targetAgent = (data.metadata as Record<string, unknown>)?.target_agent as string;
          setActiveAgent(targetAgent);
          break;

        case "tool_use":
          // Agent is using a tool — could show in UI
          break;

        case "done":
          setIsThinking(false);
          setAgentStatus(agentId, "idle");
          break;

        case "error":
          setIsThinking(false);
          addMessage(CONVERSATION_ID, {
            id: `err-${Date.now()}`,
            role: "system",
            content: `Error: ${content}`,
            timestamp: Date.now(),
          });
          break;
      }
    },
    [addMessage, appendToLast, isThinking, setAgentStatus]
  );

  const { connected, send } = useWebSocket({
    url: "/api/conversations/ws/axon",
    onMessage: handleWsMessage,
  });

  // Request greeting on first connect
  useEffect(() => {
    if (connected && !hasGreetedRef.current && conversationMessages.length === 0) {
      hasGreetedRef.current = true;
      send({ type: "greeting" });
    }
  }, [connected, send, conversationMessages.length]);

  // Auto-scroll
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
    send({ type: "message", content });
  };

  const axonAgent = agents.find((a) => a.id === "axon");
  const currentAgent = agents.find((a) => a.id === activeAgent) || axonAgent;

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="border-b border-gray-800 bg-gray-900 px-6 py-4">
        <div className="flex items-center gap-3">
          <div
            className="w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold text-white"
            style={{ backgroundColor: "#8B5CF6" }}
          >
            A
          </div>
          <div>
            <h2 className="text-lg font-semibold text-white">Axon</h2>
            <p className="text-xs text-gray-500">
              {connected ? "Connected" : "Connecting..."}
            </p>
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {conversationMessages.map((msg) => (
          <ChatMessage key={msg.id} message={msg} />
        ))}
        {isThinking && currentAgent && (
          <ThinkingIndicator
            color={currentAgent.ui.color}
            agentName={currentAgent.name}
          />
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <ChatInput
        onSend={handleSend}
        placeholder="Message Axon... (use @name to address a specific agent)"
        disabled={!connected}
      />
    </div>
  );
}
