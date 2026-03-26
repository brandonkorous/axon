import { useCallback, useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { ChatMessage } from "../Conversation/ChatMessage";
import { ChatInput } from "../Conversation/ChatInput";
import { ConversationSwitcher } from "../Conversation/ConversationSwitcher";
import { ToolUseBadge } from "../Conversation/ToolUseBadge";
import { ThinkingIndicator } from "../Sparkle/ThinkingIndicator";
import { useConversationStore } from "../../stores/conversationStore";
import { useAgentStore } from "../../stores/agentStore";
import { useWebSocket } from "../../hooks/useWebSocket";
import { useConversationSwitching } from "../../hooks/useConversationSwitching";
import { playAudioBase64 } from "../../hooks/useVoice";
import { DEFAULT_AGENT_COLOR } from "../../constants/theme";

const AGENT_ID = "axon";

export function AxonView() {
  const { messages, addMessage, appendToLast } = useConversationStore();
  const { agents, setAgentStatus } = useAgentStore();
  const [isThinking, setIsThinking] = useState(false);
  const isThinkingRef = useRef(false);
  const [activeAgent, setActiveAgent] = useState<string>("axon");
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const hasGreetedRef = useRef(false);
  const historyLoadedRef = useRef(false);
  const switchedHandlerRef = useRef<(data: Record<string, unknown>) => void>(() => {});

  const conversationMessages = messages[AGENT_ID] || [];

  const handleWsMessage = useCallback(
    (data: Record<string, unknown>) => {
      const type = data.type as string;
      const agentId = (data.agent_id as string) || "axon";
      const content = (data.content as string) || "";

      switch (type) {
        case "thinking":
          setIsThinking(true);
          isThinkingRef.current = true;
          setActiveAgent(agentId);
          setAgentStatus(agentId, "thinking");
          break;

        case "text":
          if (isThinkingRef.current) {
            setIsThinking(false);
            isThinkingRef.current = false;
            addMessage(AGENT_ID, {
              id: `msg-${Date.now()}`,
              role: "assistant",
              content,
              agentId,
              timestamp: Date.now(),
            });
          } else {
            appendToLast(AGENT_ID, content);
          }
          break;

        case "route": {
          const meta = data.metadata as Record<string, unknown> | undefined;
          const targetAgent = meta?.target_agent as string;
          const context = meta?.context as string;
          setActiveAgent(targetAgent);

          const targetInfo = agents.find((a) => a.id === targetAgent);
          const targetName = targetInfo?.name || targetAgent;
          addMessage(AGENT_ID, {
            id: `route-${Date.now()}`,
            role: "system",
            content: `**Axon** → **${targetName}**${context ? `: ${context}` : ""}`,
            timestamp: Date.now(),
            metadata: { type: "delegation", target: targetAgent },
          });
          break;
        }

        case "tool_use": {
          const meta = data.metadata as Record<string, unknown> | undefined;
          const toolName = (meta?.tool as string) || content;
          addMessage(AGENT_ID, {
            id: `tool-${Date.now()}-${Math.random()}`,
            role: "system",
            content: toolName,
            timestamp: Date.now(),
            metadata: { type: "tool_use", tool: toolName, agent_id: agentId },
          });
          break;
        }

        case "tool_result":
          break;

        case "huddle": {
          const meta = data.metadata as Record<string, unknown> | undefined;
          const topic = meta?.topic as string;
          const mode = meta?.mode as string;
          addMessage(AGENT_ID, {
            id: `huddle-${Date.now()}`,
            role: "system",
            content: `**Huddle started** — ${topic}${mode && mode !== "standard" ? ` (${mode})` : ""}`,
            timestamp: Date.now(),
            metadata: { type: "huddle" },
          });
          break;
        }

        case "transcription":
          if (content) {
            addMessage(AGENT_ID, {
              id: `user-voice-${Date.now()}`,
              role: "user",
              content: `🎤 ${content}`,
              timestamp: Date.now(),
            });
          }
          break;

        case "audio_response":
          if (data.audio) {
            playAudioBase64(data.audio as string).catch(() => {});
          }
          break;

        case "switched":
          switchedHandlerRef.current(data);
          break;

        case "done":
          setIsThinking(false);
          isThinkingRef.current = false;
          setAgentStatus(agentId, "idle");
          break;

        case "error":
          setIsThinking(false);
          isThinkingRef.current = false;
          addMessage(AGENT_ID, {
            id: `err-${Date.now()}`,
            role: "system",
            content: `Error: ${content}`,
            timestamp: Date.now(),
          });
          break;
      }
    },
    [addMessage, appendToLast, setAgentStatus, agents]
  );

  const { connected, send } = useWebSocket({
    url: "/api/conversations/ws/axon",
    onMessage: handleWsMessage,
  });

  const {
    conversations,
    activeId,
    createConversation,
    switchConversation,
    deleteConversation,
    handleSwitched,
  } = useConversationSwitching({
    agentId: AGENT_ID,
    send,
    apiPrefix: "conversations/axon",
  });

  switchedHandlerRef.current = (data: Record<string, unknown>) => {
    handleSwitched(data);
    const history = data.messages as unknown[];
    if (!historyLoadedRef.current) {
      historyLoadedRef.current = true;
      if (!hasGreetedRef.current && (!history || history.length === 0)) {
        hasGreetedRef.current = true;
        send({ type: "greeting" });
      }
    }
  };

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [conversationMessages.length, isThinking]);

  const handleSend = (content: string) => {
    addMessage(AGENT_ID, {
      id: `user-${Date.now()}`,
      role: "user",
      content,
      timestamp: Date.now(),
    });
    send({ type: "message", content });
  };

  const handleAudio = (audioBase64: string, sampleRate: number, format: string) => {
    send({ type: "audio", audio: audioBase64, sample_rate: sampleRate, format });
  };

  const axonAgent = agents.find((a) => a.id === "axon");
  const currentAgent = agents.find((a) => a.id === activeAgent) || axonAgent;

  return (
    <div className="flex flex-col h-full">
      <div className="border-b border-neutral bg-base-200 px-6 py-4">
        <div className="flex items-center gap-3">
          <div
            className="w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold text-white bg-primary"
            aria-hidden="true"
          >
            A
          </div>
          <div className="flex-1">
            <div className="flex items-center gap-2">
              <h2 className="text-lg font-semibold text-base-content">Axon</h2>
              <ConversationSwitcher
                conversations={conversations}
                activeId={activeId}
                onSwitch={switchConversation}
                onCreate={createConversation}
                onDelete={deleteConversation}
              />
            </div>
            <p className="text-xs text-base-content/60">
              {connected ? "Connected" : "Connecting..."}
            </p>
          </div>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {conversationMessages.map((msg) => {
          if (msg.metadata?.type === "delegation") {
            return (
              <DelegationBanner
                key={msg.id}
                content={msg.content}
                targetAgent={agents.find((a) => a.id === msg.metadata?.target)}
              />
            );
          }

          if (msg.metadata?.type === "tool_use") {
            return (
              <ToolUseBadge
                key={msg.id}
                tool={msg.metadata.tool as string}
                agentId={msg.metadata.agent_id as string}
              />
            );
          }

          if (msg.metadata?.type === "huddle") {
            return (
              <div
                key={msg.id}
                className="flex items-center gap-2 py-2 px-3 bg-warning/10 border border-warning/20 rounded-lg text-xs text-warning"
              >
                <span className="w-5 h-5 rounded-full bg-warning flex items-center justify-center text-[10px] font-bold text-warning-content shrink-0">
                  H
                </span>
                <span className="prose prose-sm">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {msg.content}
                  </ReactMarkdown>
                </span>
              </div>
            );
          }

          return <ChatMessage key={msg.id} message={msg} />;
        })}
        {isThinking && currentAgent && (
          <ThinkingIndicator
            color={currentAgent.ui.color}
            agentName={currentAgent.name}
          />
        )}
        <div ref={messagesEndRef} />
      </div>

      <ChatInput
        onSend={handleSend}
        onAudio={handleAudio}
        placeholder="Message Axon... (use @name to address a specific agent)"
        disabled={!connected}
      />
    </div>
  );
}

// ── Inline Components ──────────────────────────────────────────────

interface DelegationBannerProps {
  content: string;
  targetAgent?: { name: string; ui: { color: string } };
}

function DelegationBanner({ content, targetAgent }: DelegationBannerProps) {
  const color = targetAgent?.ui.color || DEFAULT_AGENT_COLOR;

  return (
    <div
      className="flex items-center gap-2 py-2 px-3 rounded-lg text-xs border"
      style={{
        backgroundColor: `${color}10`,
        borderColor: `${color}30`,
        color: color,
      }}
    >
      <svg
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth={2}
        className="w-4 h-4 shrink-0"
        aria-hidden="true"
      >
        <path d="M5 12h14M12 5l7 7-7 7" />
      </svg>
      <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
    </div>
  );
}

