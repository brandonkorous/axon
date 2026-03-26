import { useCallback, useEffect, useRef, useState } from "react";
import { useParams } from "react-router-dom";
import { ChatMessage } from "./ChatMessage";
import { ChatInput } from "./ChatInput";
import { ConversationSwitcher } from "./ConversationSwitcher";
import { ToolUseBadge } from "./ToolUseBadge";
import { WorkingIndicator } from "./WorkingIndicator";
import { ThinkingIndicator } from "../Sparkle/ThinkingIndicator";
import { AgentControls } from "../AgentControls/AgentControls";
import { StatusBadge } from "../AgentControls/AgentControls";
import { useConversationStore } from "../../stores/conversationStore";
import { useAgentStore } from "../../stores/agentStore";
import { useWebSocket } from "../../hooks/useWebSocket";
import { useConversationSwitching } from "../../hooks/useConversationSwitching";
import { playAudioBase64 } from "../../hooks/useVoice";
import { orgApiPath } from "../../stores/orgStore";
import { DocumentDrawer } from "../Documents/DocumentDrawer";

export function AgentView() {
  const { agentId } = useParams<{ agentId: string }>();
  const {
    messages,
    addMessage,
    appendToLast,
    runningTasks,
    addRunningTask,
    removeRunningTask,
    setRunningTasks,
    appendTaskLog,
    clearTaskLog,
  } = useConversationStore();
  const { agents, setAgentStatus } = useAgentStore();
  const [isThinking, setIsThinking] = useState(false);
  const [openDocPath, setOpenDocPath] = useState<string | null>(null);
  const isThinkingRef = useRef(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const hasGreetedRef = useRef<string | null>(null);
  const historyLoadedRef = useRef(false);
  const switchedHandlerRef = useRef<(data: Record<string, unknown>) => void>(() => {});

  const agent = agents.find((a) => a.id === agentId);
  const conversationMessages = messages[agentId || ""] || [];
  const agentRunningTasks = runningTasks[agentId || ""] || [];

  const handleWsMessage = useCallback(
    (data: Record<string, unknown>) => {
      if (!agentId) return;
      const type = data.type as string;
      const content = (data.content as string) || "";

      const taskPath = data.task_path as string | undefined;

      switch (type) {
        case "thinking":
          setIsThinking(true);
          isThinkingRef.current = true;
          setAgentStatus(agentId, "thinking");
          break;
        case "text":
          // Capture task execution output as log
          if (taskPath) {
            appendTaskLog(agentId, taskPath, content);
          }
          if (isThinkingRef.current) {
            setIsThinking(false);
            isThinkingRef.current = false;
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
        case "tool_use": {
          const meta = data.metadata as Record<string, unknown> | undefined;
          const toolName = (meta?.tool as string) || content;
          addMessage(agentId, {
            id: `tool-${Date.now()}-${Math.random()}`,
            role: "system",
            content: toolName,
            timestamp: Date.now(),
            metadata: { type: "tool_use", tool: toolName },
          });
          break;
        }
        case "transcription":
          if (content) {
            addMessage(agentId, {
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
        case "task_update": {
          const tPath = data.task_path as string;
          const taskTitle = data.task_title as string;
          const status = data.status as string;
          if (status === "in_progress" || status === "executing") {
            addRunningTask(agentId, {
              path: tPath,
              title: taskTitle,
              agentId,
              startedAt: Date.now(),
            });
          } else if (status === "done" || status === "failed") {
            removeRunningTask(agentId, tPath);
            clearTaskLog(agentId, tPath);
          }
          break;
        }
        case "command_result": {
          const success = data.success as boolean;
          const command = data.command as string;
          addMessage(agentId, {
            id: `cmd-${Date.now()}`,
            role: "system",
            content,
            timestamp: Date.now(),
            metadata: { type: "command_result", command, success },
          });
          break;
        }
        case "done":
          setIsThinking(false);
          isThinkingRef.current = false;
          setAgentStatus(agentId, "idle");
          break;
        case "error":
          setIsThinking(false);
          isThinkingRef.current = false;
          addMessage(agentId, {
            id: `err-${Date.now()}`,
            role: "system",
            content: `Error: ${content}`,
            timestamp: Date.now(),
          });
          break;
      }
    },
    [agentId, addMessage, appendToLast, setAgentStatus, addRunningTask, removeRunningTask, appendTaskLog, clearTaskLog]
  );

  const { connected, send } = useWebSocket({
    url: `/api/conversations/ws/${agentId}`,
    onMessage: handleWsMessage,
    autoConnect: !!agentId,
  });

  const {
    conversations,
    activeId,
    createConversation,
    switchConversation,
    deleteConversation,
    handleSwitched,
  } = useConversationSwitching({
    agentId: agentId || "",
    send,
    apiPrefix: `conversations/${agentId}`,
  });

  switchedHandlerRef.current = (data: Record<string, unknown>) => {
    handleSwitched(data);
    const history = data.messages as unknown[];
    // After initial history load, send greeting if conversation is empty
    if (!historyLoadedRef.current) {
      historyLoadedRef.current = true;
      if (agentId && hasGreetedRef.current !== agentId && (!history || history.length === 0)) {
        hasGreetedRef.current = agentId;
        send({ type: "greeting" });
      }
    }
  };

  // Reset history loaded flag when agent changes
  useEffect(() => {
    historyLoadedRef.current = false;
  }, [agentId]);

  // Recover running tasks on connect (handles page refresh mid-task)
  useEffect(() => {
    if (!connected || !agentId) return;
    fetch(orgApiPath(`tasks?assignee=${agentId}&status=in_progress`))
      .then((res) => res.json())
      .then((tasks: Array<Record<string, string>>) => {
        const recovered = tasks
          .filter((t) => t.conversation_id)
          .map((t) => ({
            path: t.path,
            title: t.name || "Task",
            agentId: agentId,
            startedAt: new Date(t.updated_at || t.created_at).getTime(),
          }));
        setRunningTasks(agentId, recovered);
      })
      .catch(() => {});
  }, [connected, agentId, setRunningTasks]);

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

  const handleCommand = (name: string, args: string) => {
    if (!agentId) return;
    addMessage(agentId, {
      id: `user-cmd-${Date.now()}`,
      role: "user",
      content: `/${name}${args ? " " + args : ""}`,
      timestamp: Date.now(),
      metadata: { type: "command" },
    });
    send({ type: "command", name, args });
  };

  const handleAudio = (audioBase64: string, sampleRate: number, format: string) => {
    send({ type: "audio", audio: audioBase64, sample_rate: sampleRate, format });
  };

  if (!agent) {
    return (
      <div className="flex items-center justify-center h-full text-base-content/60">
        Agent not found
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      <div className="border-b border-neutral bg-base-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div
              className="w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold text-white"
              style={{ backgroundColor: agent.ui.color }}
              aria-hidden="true"
            >
              {agent.name[0]}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-lg font-semibold text-base-content">{agent.name}</h2>
                {agent.lifecycle && <StatusBadge status={agent.lifecycle.status} />}
                <ConversationSwitcher
                  conversations={conversations}
                  activeId={activeId}
                  onSwitch={switchConversation}
                  onCreate={createConversation}
                  onDelete={deleteConversation}
                />
              </div>
              <p className="text-xs text-base-content/60">{agent.title} — {agent.tagline}</p>
            </div>
          </div>
        </div>
        {agent.lifecycle && (
          <div className="mt-3">
            <AgentControls agentId={agent.id} lifecycle={agent.lifecycle} agent={agent} />
          </div>
        )}
      </div>

      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {conversationMessages.map((msg) =>
          msg.metadata?.type === "tool_use" ? (
            <ToolUseBadge
              key={msg.id}
              tool={msg.metadata.tool as string}
              agentId={agent.id}
            />
          ) : (
            <ChatMessage key={msg.id} message={msg} onDocumentOpen={setOpenDocPath} />
          )
        )}
        {isThinking && (
          <ThinkingIndicator color={agent.ui.color} agentName={agent.name} />
        )}
        <div ref={messagesEndRef} />
      </div>

      {agentRunningTasks.length > 0 && (
        <WorkingIndicator chatId={agentId!} tasks={agentRunningTasks} color={agent.ui.color} />
      )}

      <ChatInput
        onSend={handleSend}
        onCommand={handleCommand}
        onAudio={handleAudio}
        agents={agents}
        placeholder={`Message ${agent.name}...`}
        disabled={!connected}
      />

      {openDocPath && agentId && (
        <DocumentDrawer
          vaultId={agentId}
          filePath={openDocPath}
          onClose={() => setOpenDocPath(null)}
          onNavigate={(path) => setOpenDocPath(path)}
        />
      )}
    </div>
  );
}
