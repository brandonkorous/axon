import { memo, useMemo, type AnchorHTMLAttributes, type ReactNode } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { ChatMessage as ChatMessageType } from "../../stores/conversationStore";
import { useAgentStore } from "../../stores/agentStore";
import { parseVaultDocLink } from "./docLinkUtils";

interface Props {
  message: ChatMessageType;
  onDocumentOpen?: (filePath: string) => void;
}

export const ChatMessage = memo(function ChatMessage({ message, onDocumentOpen }: Props) {
  const { agents } = useAgentStore();
  const agent = agents.find((a) => a.id === message.agentId);

  const isUser = message.role === "user";
  const agentColor = agent?.ui.color || "#8B5CF6";
  const agentName = agent?.name || message.speaker || "Axon";

  const markdownComponents = useMemo(() => ({
    a: ({ href, children, ...props }: AnchorHTMLAttributes<HTMLAnchorElement> & { children?: ReactNode }) => {
      const docPath = href ? parseVaultDocLink(href) : null;
      if (docPath && onDocumentOpen) {
        return (
          <a
            {...props}
            href={href}
            onClick={(e) => {
              e.preventDefault();
              onDocumentOpen(docPath);
            }}
            className="link link-accent cursor-pointer"
          >
            {children}
          </a>
        );
      }
      return (
        <a {...props} href={href} target="_blank" rel="noopener noreferrer">
          {children}
        </a>
      );
    },
  }), [onDocumentOpen]);

  return (
    <div className={`flex gap-3 ${isUser ? "flex-row-reverse" : ""}`}>
      <div
        className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold text-white shrink-0 ${isUser ? "bg-neutral" : ""}`}
        style={isUser ? undefined : { backgroundColor: agentColor }}
        aria-hidden="true"
      >
        {isUser ? "You" : agentName[0]}
      </div>

      <div
        className={`max-w-[80%] rounded-xl px-4 py-3 ${
          isUser
            ? "bg-secondary text-base-content"
            : "bg-base-300/50 text-base-content border border-neutral/50"
        }`}
      >
        {!isUser && (
          <div className="text-xs font-semibold mb-1" style={{ color: agentColor }}>
            {agentName}
            {message.target && (
              <span className="text-neutral-content"> → {message.target}</span>
            )}
          </div>
        )}
        <div className="prose prose-sm prose-invert max-w-none">
          <ReactMarkdown remarkPlugins={[remarkGfm]} components={markdownComponents}>
            {message.content}
          </ReactMarkdown>
        </div>
      </div>
    </div>
  );
});
