import { useCallback, useEffect, useRef, useState } from "react";
import { useParams } from "react-router-dom";
import { ChatMessage } from "./ChatMessage";
import { ChatInput } from "./ChatInput";
import { ThinkingIndicator } from "../Sparkle/ThinkingIndicator";
import { useConversationStore } from "../../stores/conversationStore";
import { useAgentStore } from "../../stores/agentStore";
import { useWebSocket } from "../../hooks/useWebSocket";

export function AgentView() {
  const { agentId } = useParams<{ agentId: string }>();
  const { messages, addMessage, appendToLast } = useConversationStore();
  const { agents, setAgentStatus } = useAgentStore();
  const [isThinking, setIsThinking] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const hasGreetedRef = useRef<string | null>(null);

  const agent = agents.find((a) => a.id === agentId);
  const conversationMessages = messages[agentId || ""] || [];

  const handleWsMessage = useCallback(
    (data: Record<string, unknown>) => {
      if (!agentId) return;
      const type = data.type as string;
      const content = (data.content as string) || "";

      switch (type) {
        case "thinking":
          setIsThinking(true);
          setAgentStatus(agentId, "thinking");
          break;
        case "text":
          if (isThinking) {
            setIsThinking(false);
            addMessage(agentId, {
              id: `msg-${Date.now()}`,
              role: "assistant",
              content,
              agentId,
              timestamp: Date.now(),
            });
          } else {
            appendToLast(agentId, content);
          }
          break;
        case "done":
          setIsThinking(false);
          setAgentStatus(agentId, "idle");
          break;
        case "error":
          setIsThinking(false);
          addMessage(agentId, {
            id: `err-${Date.now()}`,
            role: "system",
            content: `Error: ${content}`,
            timestamp: Date.now(),
          });
          break;
      }
    },
    [agentId, addMessage, appendToLast, isThinking, setAgentStatus]
  );

  const { connected, send } = useWebSocket({
    url: `/api/conversations/ws/${agentId}`,
    onMessage: handleWsMessage,
    autoConnect: !!agentId,
  });

  useEffect(() => {
    if (connected && agentId && hasGreetedRef.current !== agentId && conversationMessages.length === 0) {
      hasGreetedRef.current = agentId;
      send({ type: "greeting" });
    }
  }, [connected, agentId, send, conversationMessages.length]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [conversationMessages.length, isThinking]);

  const handleSend = (content: string) => {
    if (!agentId) return;
    addMessage(agentId, {
      id: `user-${Date.now()}`,
      role: "user",
      content,
      timestamp: Date.now(),
    });
    send({ type: "message", content });
  };

  if (!agent) {
    return (
      <div className="flex items-center justify-center h-full text-gray-500">
        Agent not found
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      <div className="border-b border-gray-800 bg-gray-900 px-6 py-4">
        <div className="flex items-center gap-3">
          <div
            className="w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold text-white"
            style={{ backgroundColor: agent.ui.color }}
          >
            {agent.name[0]}
          </div>
          <div>
            <h2 className="text-lg font-semibold text-white">{agent.name}</h2>
            <p className="text-xs text-gray-500">{agent.title} — {agent.tagline}</p>
          </div>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {conversationMessages.map((msg) => (
          <ChatMessage key={msg.id} message={msg} />
        ))}
        {isThinking && (
          <ThinkingIndicator color={agent.ui.color} agentName={agent.name} />
        )}
        <div ref={messagesEndRef} />
      </div>

      <ChatInput
        onSend={handleSend}
        placeholder={`Message ${agent.name}...`}
        disabled={!connected}
      />
    </div>
  );
}
