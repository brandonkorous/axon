import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { ChatMessage as ChatMessageType } from "../../stores/conversationStore";
import { useAgentStore } from "../../stores/agentStore";

interface Props {
  message: ChatMessageType;
}

export function ChatMessage({ message }: Props) {
  const { agents } = useAgentStore();
  const agent = agents.find((a) => a.id === message.agentId);

  const isUser = message.role === "user";
  const agentColor = agent?.ui.color || "#8B5CF6";
  const agentName = agent?.name || message.speaker || "Axon";

  return (
    <div className={`flex gap-3 ${isUser ? "flex-row-reverse" : ""}`}>
      {/* Avatar */}
      <div
        className="w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold text-white shrink-0"
        style={{ backgroundColor: isUser ? "#6B7280" : agentColor }}
      >
        {isUser ? "You" : agentName[0]}
      </div>

      {/* Message */}
      <div
        className={`max-w-[80%] rounded-xl px-4 py-3 ${
          isUser
            ? "bg-gray-700 text-gray-100"
            : "bg-gray-800/50 text-gray-200 border border-gray-700/50"
        }`}
      >
        {!isUser && (
          <div className="text-xs font-semibold mb-1" style={{ color: agentColor }}>
            {agentName}
            {message.target && (
              <span className="text-gray-500"> → {message.target}</span>
            )}
          </div>
        )}
        <div className="prose prose-sm prose-invert max-w-none">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>
            {message.content}
          </ReactMarkdown>
        </div>
      </div>
    </div>
  );
}
