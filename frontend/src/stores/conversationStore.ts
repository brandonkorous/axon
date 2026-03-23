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

export interface RunningTask {
  path: string;
  title: string;
  agentId: string;
  startedAt: number;
}

interface ConversationStore {
  messages: Record<string, ChatMessage[]>; // keyed by agent/huddle ID
  conversationLists: Record<string, ConversationMeta[]>; // keyed by agent ID
  activeConversationId: Record<string, string>; // keyed by agent ID
  runningTasks: Record<string, RunningTask[]>; // keyed by agent ID
  taskLogs: Record<string, Record<string, string>>; // [chatId][taskPath] → log text

  addMessage: (conversationId: string, message: ChatMessage) => void;
  appendToLast: (conversationId: string, content: string) => void;
  clearMessages: (conversationId: string) => void;
  replaceMessages: (conversationId: string, messages: ChatMessage[]) => void;
  setConversationList: (agentId: string, conversations: ConversationMeta[]) => void;
  setActiveConversation: (agentId: string, conversationId: string) => void;
  addRunningTask: (agentId: string, task: RunningTask) => void;
  removeRunningTask: (agentId: string, taskPath: string) => void;
  setRunningTasks: (agentId: string, tasks: RunningTask[]) => void;
  appendTaskLog: (chatId: string, taskPath: string, content: string) => void;
  clearTaskLog: (chatId: string, taskPath: string) => void;
}

let messageCounter = 0;

export const useConversationStore = create<ConversationStore>((set) => ({
  messages: {},
  conversationLists: {},
  activeConversationId: {},
  runningTasks: {},
  taskLogs: {},

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

  addRunningTask: (agentId, task) =>
    set((state) => {
      const existing = state.runningTasks[agentId] || [];
      // Avoid duplicates
      if (existing.some((t) => t.path === task.path)) return state;
      return {
        runningTasks: {
          ...state.runningTasks,
          [agentId]: [...existing, task],
        },
      };
    }),

  removeRunningTask: (agentId, taskPath) =>
    set((state) => ({
      runningTasks: {
        ...state.runningTasks,
        [agentId]: (state.runningTasks[agentId] || []).filter(
          (t) => t.path !== taskPath,
        ),
      },
    })),

  setRunningTasks: (agentId, tasks) =>
    set((state) => ({
      runningTasks: { ...state.runningTasks, [agentId]: tasks },
    })),

  appendTaskLog: (chatId, taskPath, content) =>
    set((state) => {
      const chatLogs = state.taskLogs[chatId] || {};
      return {
        taskLogs: {
          ...state.taskLogs,
          [chatId]: {
            ...chatLogs,
            [taskPath]: (chatLogs[taskPath] || "") + content,
          },
        },
      };
    }),

  clearTaskLog: (chatId, taskPath) =>
    set((state) => {
      const chatLogs = { ...(state.taskLogs[chatId] || {}) };
      delete chatLogs[taskPath];
      return {
        taskLogs: { ...state.taskLogs, [chatId]: chatLogs },
      };
    }),
}));
