import { create } from "zustand";

export interface ChatMessage {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  agentId?: string;
  speaker?: string; // For boardroom: "marcus", "raj", "diana", "table"
  target?: string; // For boardroom: "marcus → raj"
  timestamp: number;
  metadata?: Record<string, unknown>;
}

interface ConversationStore {
  messages: Record<string, ChatMessage[]>; // keyed by agent/boardroom ID
  addMessage: (conversationId: string, message: ChatMessage) => void;
  appendToLast: (conversationId: string, content: string) => void;
  clearMessages: (conversationId: string) => void;
}

let messageCounter = 0;

export const useConversationStore = create<ConversationStore>((set) => ({
  messages: {},

  addMessage: (conversationId, message) =>
    set((state) => ({
      messages: {
        ...state.messages,
        [conversationId]: [
          ...(state.messages[conversationId] || []),
          { ...message, id: message.id || `msg-${++messageCounter}` },
        ],
      },
    })),

  appendToLast: (conversationId, content) =>
    set((state) => {
      const msgs = state.messages[conversationId] || [];
      if (msgs.length === 0) return state;
      const last = msgs[msgs.length - 1];
      return {
        messages: {
          ...state.messages,
          [conversationId]: [
            ...msgs.slice(0, -1),
            { ...last, content: last.content + content },
          ],
        },
      };
    }),

  clearMessages: (conversationId) =>
    set((state) => ({
      messages: { ...state.messages, [conversationId]: [] },
    })),
}));
