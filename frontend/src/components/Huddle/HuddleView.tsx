import { useCallback, useEffect, useRef, useState } from "react";
import { ChatMessage } from "../Conversation/ChatMessage";
import { ChatInput } from "../Conversation/ChatInput";
import { ConversationSwitcher } from "../Conversation/ConversationSwitcher";
import { WorkingIndicator } from "../Conversation/WorkingIndicator";
import { ThinkingIndicator } from "../Sparkle/ThinkingIndicator";
import { useConversationStore } from "../../stores/conversationStore";
import { useWebSocket } from "../../hooks/useWebSocket";
import { useConversationSwitching } from "../../hooks/useConversationSwitching";
import { orgApiPath } from "../../stores/orgStore";

const MODES = [
  { id: "standard", label: "Standard" },
  { id: "vote", label: "Vote" },
  { id: "devils_advocate", label: "Devil's Advocate" },
  { id: "pressure_test", label: "Pressure Test" },
  { id: "quick_take", label: "Quick Take" },
  { id: "decision", label: "Decision" },
];

const AGENT_ID = "huddle";

export function HuddleView() {
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
  const [isThinking, setIsThinking] = useState(false);
  const [mode, setMode] = useState("standard");
  const currentSpeakerRef = useRef<string | null>(null);
  const isThinkingRef = useRef(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const switchedHandlerRef = useRef<(data: Record<string, unknown>) => void>(() => {});

  const conversationMessages = messages[AGENT_ID] || [];
  const huddleRunningTasks = runningTasks[AGENT_ID] || [];

  const handleWsMessage = useCallback(
    (data: Record<string, unknown>) => {
      const type = data.type as string;
      const speaker = data.speaker as string | null;
      const target = data.target as string | null;
      const content = (data.content as string) || "";
      const taskPath = data.task_path as string | undefined;

      switch (type) {
        case "thinking":
          setIsThinking(true);
          isThinkingRef.current = true;
          break;
        case "text":
          // Capture task execution output as log
          if (taskPath) {
            appendTaskLog(AGENT_ID, taskPath, content);
          }
          if (isThinkingRef.current || speaker !== currentSpeakerRef.current) {
            setIsThinking(false);
            isThinkingRef.current = false;
            currentSpeakerRef.current = speaker;
            addMessage(AGENT_ID, {
              id: `msg-${Date.now()}-${Math.random()}`,
              role: "assistant",
              content,
              agentId: speaker || undefined,
              speaker: speaker || undefined,
              target: target || undefined,
              timestamp: Date.now(),
            });
          } else {
            appendToLast(AGENT_ID, content);
          }
          break;
        case "task_update": {
          const tPath = data.task_path as string;
          const taskTitle = data.task_title as string;
          const status = data.status as string;
          if (status === "in_progress" || status === "executing") {
            addRunningTask(AGENT_ID, {
              path: tPath,
              title: taskTitle,
              agentId: (data.agent_id as string) || AGENT_ID,
              startedAt: Date.now(),
            });
          } else if (status === "done" || status === "failed") {
            removeRunningTask(AGENT_ID, tPath);
            clearTaskLog(AGENT_ID, tPath);
          }
          break;
        }
        case "switched":
          switchedHandlerRef.current(data);
          break;
        case "done":
          setIsThinking(false);
          isThinkingRef.current = false;
          currentSpeakerRef.current = null;
          break;
      }
    },
    [addMessage, appendToLast, addRunningTask, removeRunningTask, appendTaskLog, clearTaskLog]
  );

  const { connected, send } = useWebSocket({
    url: "/api/huddle/ws",
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
    apiPrefix: "huddle",
  });

  switchedHandlerRef.current = handleSwitched;

  // Recover running tasks on connect (handles page refresh mid-task)
  useEffect(() => {
    if (!connected) return;
    fetch(orgApiPath(`tasks?ws_target=huddle&status=in_progress`))
      .then((res) => res.json())
      .then((tasks: Array<Record<string, string>>) => {
        const recovered = tasks
          .filter((t) => t.conversation_id)
          .map((t) => ({
            path: t.path,
            title: t.name || "Task",
            agentId: t.assignee || AGENT_ID,
            startedAt: new Date(t.updated_at || t.created_at).getTime(),
          }));
        setRunningTasks(AGENT_ID, recovered);
      })
      .catch(() => {});
  }, [connected, setRunningTasks]);

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
    send({ type: "message", content, mode });
  };

  const handleAudio = (audioBase64: string, sampleRate: number, format: string) => {
    send({ type: "audio", audio: audioBase64, sample_rate: sampleRate, format });
  };

  return (
    <div className="flex flex-col h-full">
      <div className="border-b border-neutral bg-base-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-warning flex items-center justify-center text-sm font-bold text-warning-content">
              H
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-lg font-semibold text-base-content">The Huddle</h2>
                <ConversationSwitcher
                  conversations={conversations}
                  activeId={activeId}
                  onSwitch={switchConversation}
                  onCreate={createConversation}
                  onDelete={deleteConversation}
                />
              </div>
              <p className="text-xs text-base-content/60">Group advisory session</p>
            </div>
          </div>

          <div className="flex gap-1" role="radiogroup" aria-label="Discussion mode">
            {MODES.map((m) => (
              <button
                key={m.id}
                onClick={() => setMode(m.id)}
                role="radio"
                aria-checked={mode === m.id}
                className={`btn btn-xs ${
                  mode === m.id
                    ? "btn-soft btn-warning"
                    : "btn-ghost"
                }`}
              >
                {m.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {conversationMessages.map((msg) => (
          <ChatMessage key={msg.id} message={msg} />
        ))}
        {isThinking && (
          <ThinkingIndicator color="#F59E0B" agentName="Huddle" />
        )}
        <div ref={messagesEndRef} />
      </div>

      {huddleRunningTasks.length > 0 && (
        <WorkingIndicator chatId={AGENT_ID} tasks={huddleRunningTasks} color="#F59E0B" />
      )}

      <ChatInput
        onSend={handleSend}
        onAudio={handleAudio}
        placeholder="What should we discuss?"
        disabled={!connected}
      />
    </div>
  );
}
