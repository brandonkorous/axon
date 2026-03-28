import { useCallback, useEffect, useRef, useState } from "react";
import { useParams } from "react-router-dom";
import { ChatMessage } from "./ChatMessage";
import { ChatInput } from "./ChatInput";
import { ConversationSwitcher } from "./ConversationSwitcher";
import { ToolUseBadge } from "./ToolUseBadge";
import { AgentActivityBadge } from "./AgentActivityBadge";
import { WorkingIndicator } from "./WorkingIndicator";
import { ThinkingIndicator } from "../Sparkle/ThinkingIndicator";
import { AgentControls } from "../AgentControls/AgentControls";
import { StatusBadge } from "../AgentControls/AgentControls";
import { useConversationStore } from "../../stores/conversationStore";
import { useAgentStore } from "../../stores/agentStore";
import { useAgentRuntimeStore, useAgentRuntime } from "../../stores/agentRuntimeStore";
import { useWebSocket } from "../../hooks/useWebSocket";
import { useConversationSwitching } from "../../hooks/useConversationSwitching";
import { playAudioBase64 } from "../../hooks/useVoice";
import { orgApiPath } from "../../stores/orgStore";
import { DocumentDrawer } from "../Documents/DocumentDrawer";

export function AgentView() {
  const { agentId } = useParams<{ agentId: string }>();
  const { messages, addMessage, appendToLast, replaceLastMessage } = useConversationStore();
  const { agents } = useAgentStore();
  const runtime = useAgentRuntime(agentId || "");
  const [openDocPath, setOpenDocPath] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const hasGreetedRef = useRef<string | null>(null);
  const historyLoadedRef = useRef(false);
  const switchedHandlerRef = useRef<(data: Record<string, unknown>) => void>(() => {});

  const agent = agents.find((a) => a.id === agentId);
  const conversationMessages = messages[agentId || ""] || [];

  const handleWsMessage = useCallback(
    (data: Record<string, unknown>) => {
      if (!agentId) return;
      const type = data.type as string;
      const content = (data.content as string) || "";
      const taskPath = data.task_path as string | undefined;
      const rs = useAgentRuntimeStore.getState();

      switch (type) {
        case "thinking":
          rs.setThinking(agentId, true, "chat");
          break;
        case "ack":
          // Quick acknowledgment from local model — show immediately
          rs.setThinking(agentId, false);
          addMessage(agentId, {
            id: `ack-${Date.now()}`,
            role: "assistant",
            content,
            agentId,
            timestamp: Date.now(),
            metadata: { type: "ack" },
          });
          // Re-enter thinking state so the indicator shows while vault loads
          rs.setThinking(agentId, true, "chat");
          break;
        case "text":
          if (taskPath) {
            rs.appendTaskLog(agentId, taskPath, content);
          }
          if (rs.agents[agentId]?.thinking) {
            rs.setThinking(agentId, false);
            // Replace ack message with real response if present
            const msgs = useConversationStore.getState().messages[agentId] || [];
            const lastMsg = msgs[msgs.length - 1];
            if (lastMsg?.metadata?.type === "ack") {
              replaceLastMessage(agentId, {
                id: `msg-${Date.now()}`,
                role: "assistant",
                content,
                agentId,
                timestamp: Date.now(),
              });
            } else {
              addMessage(agentId, {
                id: `msg-${Date.now()}`,
                role: "assistant",
                content,
                agentId,
                timestamp: Date.now(),
              });
            }
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
            rs.addRunningTask(agentId, {
              path: tPath,
              title: taskTitle,
              agentId,
              startedAt: Date.now(),
            });
          } else if (status === "done" || status === "failed") {
            rs.removeRunningTask(agentId, tPath);
            rs.clearTaskLog(agentId, tPath);
          }
          break;
        }
        case "agent_activated": {
          const meta = data.metadata as Record<string, unknown> | undefined;
          addMessage(agentId, {
            id: `agent-act-${Date.now()}`,
            role: "system",
            content: (meta?.task_description as string) || content,
            timestamp: Date.now(),
            metadata: {
              type: "agent_activated",
              target_agent: meta?.target_agent as string,
              mode: meta?.mode as string,
            },
          });
          break;
        }
        case "agent_result": {
          const meta = data.metadata as Record<string, unknown> | undefined;
          addMessage(agentId, {
            id: `agent-res-${Date.now()}`,
            role: "system",
            content: (meta?.task_summary as string) || content,
            timestamp: Date.now(),
            metadata: {
              type: "agent_result",
              source_agent: meta?.source_agent as string,
              status: meta?.status as string,
            },
          });
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
          rs.setThinking(agentId, false);
          break;
        case "error":
          rs.setThinking(agentId, false);
          addMessage(agentId, {
            id: `err-${Date.now()}`,
            role: "system",
            content: `Error: ${content}`,
            timestamp: Date.now(),
          });
          break;
      }
    },
    [agentId, addMessage, appendToLast, replaceLastMessage]
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
        useAgentRuntimeStore.getState().setRunningTasks(agentId, recovered);
      })
      .catch(() => {});
  }, [connected, agentId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [conversationMessages.length, runtime.thinking]);

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
      <div className="bg-base-200 px-6 py-4">
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
                <h2 className="text-lg font-semibold text-base-content">{agent.name}{agent.title_tag && <span className="text-base-content/50 font-normal text-sm ml-2">({agent.title_tag})</span>}</h2>
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
        {conversationMessages.map((msg) => {
          const isFromHistory = msg.id.startsWith("hist-");

          if (msg.metadata?.type === "tool_use") {
            return (
              <ToolUseBadge
                key={msg.id}
                tool={msg.metadata.tool as string}
                agentId={agent.id}
                live={!isFromHistory}
              />
            );
          }

          if (msg.metadata?.type === "agent_activated" || msg.metadata?.type === "agent_result") {
            return (
              <AgentActivityBadge
                key={msg.id}
                type={msg.metadata.type as "agent_activated" | "agent_result"}
                agentId={(msg.metadata.target_agent || msg.metadata.source_agent) as string}
                taskSummary={msg.content}
                mode={msg.metadata.mode as string}
                status={msg.metadata.status as string}
                live={!isFromHistory}
              />
            );
          }

          return <ChatMessage key={msg.id} message={msg} onDocumentOpen={setOpenDocPath} />;
        })}
        {runtime.thinking && (
          <ThinkingIndicator color={agent.ui.color} agentName={agent.name} />
        )}
        <div ref={messagesEndRef} />
      </div>

      {runtime.runningTasks.length > 0 && (
        <WorkingIndicator tasks={runtime.runningTasks} color={agent.ui.color} />
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
