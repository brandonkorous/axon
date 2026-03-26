import { create } from "zustand";

export interface ChatMessage {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  agentId?: string;
  speaker?: string; // For huddle: "marcus", "raj", "diana", "table"
  target?: string; // For huddle: "marcus → raj"
  timestamp: number;
  metadata?: Record<string, unknown>;
}

export interface ConversationMeta {
  id: string;
  title: string;
  created_at: number;
  last_message_at: number;
  message_count: number;
}

interface ConversationStore {
  messages: Record<string, ChatMessage[]>; // keyed by agent/huddle ID
  conversationLists: Record<string, ConversationMeta[]>; // keyed by agent ID
  activeConversationId: Record<string, string>; // keyed by agent ID

  addMessage: (conversationId: string, message: ChatMessage) => void;
  appendToLast: (conversationId: string, content: string) => void;
  appendToSpeaker: (conversationId: string, speaker: string, content: string) => void;
  clearMessages: (conversationId: string) => void;
  replaceMessages: (conversationId: string, messages: ChatMessage[]) => void;
  setConversationList: (agentId: string, conversations: ConversationMeta[]) => void;
  setActiveConversation: (agentId: string, conversationId: string) => void;
}

let messageCounter = 0;

export const useConversationStore = create<ConversationStore>((set) => ({
  messages: {},
  conversationLists: {},
  activeConversationId: {},

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

  appendToSpeaker: (conversationId, speaker, content) =>
    set((state) => {
      const msgs = state.messages[conversationId];
      if (!msgs) return state;
      // Find the last message from this speaker
      let idx = -1;
      for (let i = msgs.length - 1; i >= 0; i--) {
        if (msgs[i].speaker === speaker) { idx = i; break; }
      }
      if (idx === -1) return state;
      const msg = msgs[idx];
      return {
        messages: {
          ...state.messages,
          [conversationId]: [
            ...msgs.slice(0, idx),
            { ...msg, content: msg.content + content },
            ...msgs.slice(idx + 1),
          ],
        },
      };
    }),

  clearMessages: (conversationId) =>
    set((state) => ({
      messages: { ...state.messages, [conversationId]: [] },
    })),

  replaceMessages: (conversationId, messages) =>
    set((state) => ({
      messages: { ...state.messages, [conversationId]: messages },
    })),

  setConversationList: (agentId, conversations) =>
    set((state) => ({
      conversationLists: { ...state.conversationLists, [agentId]: conversations },
    })),

  setActiveConversation: (agentId, conversationId) =>
    set((state) => ({
      activeConversationId: { ...state.activeConversationId, [agentId]: conversationId },
    })),
}));
