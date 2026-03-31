import { useCallback, useEffect, useRef, useState } from "react";
import { ChatMessage } from "../Conversation/ChatMessage";
import { ChatInput } from "../Conversation/ChatInput";
import { ConversationSwitcher } from "../Conversation/ConversationSwitcher";
import { WorkingIndicator } from "../Conversation/WorkingIndicator";
import { ThinkingIndicator } from "../Sparkle/ThinkingIndicator";
import { useConversationStore } from "../../stores/conversationStore";
import { useAgentStore } from "../../stores/agentStore";
import { useAgentRuntimeStore, useThinkingAgents } from "../../stores/agentRuntimeStore";
import { useWebSocket } from "../../hooks/useWebSocket";
import { useConversationSwitching } from "../../hooks/useConversationSwitching";
import { useShallow } from "zustand/react/shallow";

import { DEFAULT_AGENT_COLOR } from "../../constants/theme";

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
    const { messages, addMessage, appendToSpeaker } = useConversationStore();
    const { agents } = useAgentStore();
    const thinkingAgentIds = useThinkingAgents();
    const huddleRunningTasks = useAgentRuntimeStore(
        useShallow((s) => Object.values(s.agents).flatMap((a) => a.runningTasks)),
    );
    const [mode, setMode] = useState("standard");
    const activeSpeakers = useRef<Set<string>>(new Set());
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const switchedHandlerRef = useRef<(data: Record<string, unknown>) => void>(() => { });

    const conversationMessages = messages[AGENT_ID] || [];

    const handleWsMessage = useCallback(
        (data: Record<string, unknown>) => {
            const type = data.type as string;
            const speaker = data.speaker as string | null;
            const target = data.target as string | null;
            const content = (data.content as string) || "";
            const taskPath = data.task_path as string | undefined;
            const rs = useAgentRuntimeStore.getState();

            switch (type) {
                case "thinking":
                    if (speaker) {
                        rs.setThinking(speaker, true, "huddle");
                    }
                    break;
                case "text":
                    if (taskPath && speaker) {
                        rs.appendTaskLog(speaker, taskPath, content);
                    }
                    if (speaker) {
                        rs.setThinking(speaker, false);
                    }
                    if (speaker && activeSpeakers.current.has(speaker)) {
                        appendToSpeaker(AGENT_ID, speaker, content);
                    } else if (speaker) {
                        activeSpeakers.current.add(speaker);
                        addMessage(AGENT_ID, {
                            id: `msg-${Date.now()}-${Math.random()}`,
                            role: "assistant",
                            content,
                            agentId: speaker,
                            speaker,
                            target: target || undefined,
                            timestamp: Date.now(),
                        });
                    } else {
                        addMessage(AGENT_ID, {
                            id: `msg-${Date.now()}-${Math.random()}`,
                            role: "assistant",
                            content,
                            timestamp: Date.now(),
                        });
                    }
                    break;
                case "speaker_done":
                    if (speaker) {
                        rs.setThinking(speaker, false);
                        activeSpeakers.current.delete(speaker);
                    }
                    break;
                case "task_update": {
                    const tPath = data.task_path as string;
                    const taskTitle = data.task_title as string;
                    const status = data.status as string;
                    const taskAgentId = (data.agent_id as string) || AGENT_ID;
                    if (status === "in_progress") {
                        rs.addRunningTask(taskAgentId, {
                            path: tPath,
                            title: taskTitle,
                            agentId: taskAgentId,
                            startedAt: Date.now(),
                        });
                    } else if (status === "done" || status === "failed") {
                        rs.removeRunningTask(taskAgentId, tPath);
                        rs.clearTaskLog(taskAgentId, tPath);
                    }
                    break;
                }
                case "switched":
                    switchedHandlerRef.current(data);
                    break;
                case "done":
                    activeSpeakers.current.clear();
                    break;
            }
        },
        [addMessage, appendToSpeaker]
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

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [conversationMessages.length, thinkingAgentIds.length]);

    const handleSend = (content: string) => {
        addMessage(AGENT_ID, {
            id: `user-${Date.now()}`,
            role: "user",
            content,
            timestamp: Date.now(),
        });
        send({ type: "message", content, mode: mode });
    };

    const handleAudio = (audioBase64: string, sampleRate: number, format: string) => {
        send({ type: "audio", audio: audioBase64, sample_rate: sampleRate, format });
    };

    const getAgentDisplay = (speakerId: string) => {
        const agent = agents.find((a) => a.id === speakerId);
        return {
            name: agent?.name || speakerId,
            color: agent?.ui.color || DEFAULT_AGENT_COLOR,
        };
    };

    return (
        <div className="flex flex-col h-full">
            <div className="bg-base-200 px-6 py-4">
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
                            <p className="text-xs text-base-content/60">Group chat</p>
                        </div>
                    </div>

                    <div className="flex gap-1" role="radiogroup" aria-label="Discussion mode">
                        {MODES.map((m) => (
                            <button
                                key={m.id}
                                onClick={() => setMode(m.id)}
                                role="radio"
                                aria-checked={mode === m.id}
                                className={`btn btn-xs ${mode === m.id
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
                {thinkingAgentIds.map((speakerId) => {
                    const display = getAgentDisplay(speakerId);
                    return (
                        <ThinkingIndicator
                            key={speakerId}
                            color={display.color}
                            agentName={display.name}
                        />
                    );
                })}
                <div ref={messagesEndRef} />
            </div>

            {huddleRunningTasks.length > 0 && (
                <WorkingIndicator tasks={huddleRunningTasks} color="#F59E0B" />
            )}

            <ChatInput
                onSend={handleSend}
                onAudio={handleAudio}
                placeholder="Message the group, or @mention specific advisors..."
                disabled={!connected}
            />
        </div>
    );
}
