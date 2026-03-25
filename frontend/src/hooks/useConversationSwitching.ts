import { useCallback, useEffect } from "react";
import { orgApiPath } from "../stores/orgStore";
import {
  ChatMessage,
  ConversationMeta,
  useConversationStore,
} from "../stores/conversationStore";

interface UseConversationSwitchingOptions {
  /** Agent ID or "huddle" */
  agentId: string;
  /** WebSocket send function */
  send: (data: Record<string, unknown>) => void;
  /** API path prefix for conversations endpoint (e.g. "conversations/axon" or "huddle") */
  apiPrefix: string;
}

export function useConversationSwitching({
  agentId,
  send,
  apiPrefix,
}: UseConversationSwitchingOptions) {
  const {
    conversationLists,
    activeConversationId,
    setConversationList,
    setActiveConversation,
    replaceMessages,
    clearMessages,
  } = useConversationStore();

  const conversations = conversationLists[agentId] || [];
  const activeId = activeConversationId[agentId] || "";

  const fetchConversations = useCallback(async () => {
    try {
      const res = await fetch(orgApiPath(`${apiPrefix}/conversations`));
      if (!res.ok) return;
      const data = await res.json();
      setConversationList(agentId, data.conversations as ConversationMeta[]);
      if (data.active_id) {
        setActiveConversation(agentId, data.active_id);
      }
    } catch {
      // Silently fail — conversations list is non-critical
    }
  }, [agentId, apiPrefix, setConversationList, setActiveConversation]);

  useEffect(() => {
    fetchConversations();
  }, [fetchConversations]);

  const createConversation = useCallback(async () => {
    try {
      const res = await fetch(orgApiPath(`${apiPrefix}/conversations`), {
        method: "POST",
      });
      if (!res.ok) return;
      const data = await res.json();
      const newId = data.conversation_id as string;

      // Switch to the new conversation via WebSocket
      send({ type: "switch", conversation_id: newId });

      // Clear current messages immediately for snappy UX
      clearMessages(agentId);
      setActiveConversation(agentId, newId);

      // Refresh the conversation list
      await fetchConversations();
    } catch {
      // Silently fail
    }
  }, [agentId, apiPrefix, send, clearMessages, setActiveConversation, fetchConversations]);

  const switchConversation = useCallback(
    (conversationId: string) => {
      if (conversationId === activeId) return;
      send({ type: "switch", conversation_id: conversationId });

      // Clear stale messages and update active ID immediately for snappy UX
      // (history will be populated when the "switched" WS response arrives)
      clearMessages(agentId);
      setActiveConversation(agentId, conversationId);
    },
    [activeId, agentId, send, clearMessages, setActiveConversation],
  );

  const deleteConversation = useCallback(
    async (conversationId: string) => {
      try {
        const res = await fetch(
          orgApiPath(`${apiPrefix}/conversations/${conversationId}`),
          { method: "DELETE" },
        );
        if (!res.ok) return;
        const data = await res.json();

        // If we deleted the active one, the backend switched us
        if (data.active_id && data.active_id !== activeId) {
          send({ type: "switch", conversation_id: data.active_id });
          clearMessages(agentId);
          setActiveConversation(agentId, data.active_id);
        }

        await fetchConversations();
      } catch {
        // Silently fail
      }
    },
    [agentId, apiPrefix, activeId, send, clearMessages, setActiveConversation, fetchConversations],
  );

  /** Call this from the WS message handler when type === "switched" */
  const handleSwitched = useCallback(
    (data: Record<string, unknown>) => {
      const convId = data.conversation_id as string;
      const history = data.messages as Array<{
        role: string;
        content: string;
        agent_id?: string;
        timestamp: number;
        speaker?: string;
        target?: string;
      }>;

      const mapped: ChatMessage[] = (history || []).map((m, i) => ({
        id: `hist-${i}`,
        role: m.role as "user" | "assistant" | "system",
        content: m.content,
        agentId: m.agent_id || m.speaker,
        speaker: m.speaker,
        target: m.target,
        timestamp: m.timestamp * 1000,
      }));

      replaceMessages(agentId, mapped);
      setActiveConversation(agentId, convId);
      fetchConversations();
    },
    [agentId, replaceMessages, setActiveConversation, fetchConversations],
  );

  return {
    conversations,
    activeId,
    createConversation,
    switchConversation,
    deleteConversation,
    handleSwitched,
    fetchConversations,
  };
}
