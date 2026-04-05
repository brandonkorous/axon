import { memo, useMemo, type AnchorHTMLAttributes, type ReactNode } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { ChatMessage as ChatMessageType } from "../../stores/conversationStore";
import { useAgents } from "../../hooks/useAgents";
import { parseVaultDocLink } from "./docLinkUtils";
import { DEFAULT_AGENT_COLOR } from "../../constants/theme";

interface Props {
    message: ChatMessageType;
    onDocumentOpen?: (filePath: string) => void;
}

export const ChatMessage = memo(function ChatMessage({ message, onDocumentOpen }: Props) {
    const { data: agents = [] } = useAgents();
    const agent = agents.find((a) => a.id === message.agentId);

    const isUser = message.role === "user";
    const isAck = message.metadata?.type === "ack";
    const isCommandResult = message.metadata?.type === "command_result";
    const agentColor = agent?.ui.color || DEFAULT_AGENT_COLOR;
    const agentName = agent?.name || message.speaker || "Axon";

    if (isCommandResult) {
        const success = message.metadata?.success as boolean;
        const command = message.metadata?.command as string;
        return (
            <div className="flex gap-3">
                <div className="w-8 h-8 shrink-0" />
                <div
                    className={`max-w-[80%] border-l-2 pl-3 py-2 ${success !== false ? "border-success" : "border-error"
                        }`}
                >
                    <span className="badge badge-ghost badge-sm font-mono mb-1">/{command}</span>
                    <div className="text-sm text-base-content/80 whitespace-pre-wrap font-mono">
                        {message.content}
                    </div>
                </div>
            </div>
        );
    }

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
                className={`max-w-[80%] rounded-xl px-4 py-3 ${isUser
                    ? "bg-base-300/30 border border-base-300 text-base-content"
                    : isAck
                        ? "bg-primary/30 text-primary/60 border border-primary/50 italic"
                        : "bg-primary/30 text-primary border border-primary"
                    }`}
            >
                {!isUser && !isAck && (
                    <div className="text-xs font-semibold mb-1" style={{ color: agentColor }}>
                        {agentName}
                        {message.target && (
                            <span className="text-base-content/60"> → {message.target}</span>
                        )}
                    </div>
                )}
                {message.content && (
                    <div className="prose prose-sm max-w-none">
                        <ReactMarkdown remarkPlugins={[remarkGfm]} components={markdownComponents}>
                            {message.content}
                        </ReactMarkdown>
                    </div>
                )}
                {message.attachments && message.attachments.length > 0 && (
                    <MessageAttachments attachments={message.attachments} />
                )}
            </div>
        </div>
    );
});

function MessageAttachments({ attachments }: { attachments: NonNullable<ChatMessageType["attachments"]> }) {
    return (
        <div className="flex flex-wrap gap-2 mt-2">
            {attachments.map((att, i) =>
                att.type.startsWith("image/") && att.preview ? (
                    <a
                        key={`${att.name}-${i}`}
                        href={att.preview}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="block"
                    >
                        <img
                            src={att.preview}
                            alt={att.name}
                            className="rounded-lg border border-base-300 max-w-[300px] max-h-[200px] object-contain"
                        />
                    </a>
                ) : (
                    <div
                        key={`${att.name}-${i}`}
                        className="flex items-center gap-1.5 bg-base-300/40 rounded-lg px-2.5 py-1.5 border border-base-300"
                    >
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} className="w-4 h-4 text-base-content/60 shrink-0">
                            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                            <polyline points="14 2 14 8 20 8" />
                        </svg>
                        <span className="text-xs text-base-content/80">{att.name}</span>
                    </div>
                )
            )}
        </div>
    );
}
