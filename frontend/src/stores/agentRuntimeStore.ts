import { useCallback } from "react";
import { create } from "zustand";
import { useShallow } from "zustand/react/shallow";

export interface RunningTask {
  path: string;
  title: string;
  agentId: string;
  startedAt: number;
}

export interface AgentRuntimeState {
  thinking: boolean;
  context: "chat" | "axon" | "huddle" | "voice" | null;
  lastActivity: number;
  runningTasks: RunningTask[];
  taskLogs: Record<string, string>;
}

const DEFAULT_STATE: AgentRuntimeState = {
  thinking: false,
  context: null,
  lastActivity: 0,
  runningTasks: [],
  taskLogs: {},
};

interface AgentRuntimeStore {
  agents: Record<string, AgentRuntimeState>;

  setThinking: (agentId: string, thinking: boolean, context?: AgentRuntimeState["context"]) => void;
  addRunningTask: (agentId: string, task: RunningTask) => void;
  removeRunningTask: (agentId: string, taskPath: string) => void;
  setRunningTasks: (agentId: string, tasks: RunningTask[]) => void;
  appendTaskLog: (agentId: string, taskPath: string, content: string) => void;
  clearTaskLog: (agentId: string, taskPath: string) => void;
  clearAgent: (agentId: string) => void;
}

function getAgent(agents: Record<string, AgentRuntimeState>, id: string): AgentRuntimeState {
  return agents[id] ?? DEFAULT_STATE;
}

function putAgent(
  agents: Record<string, AgentRuntimeState>,
  id: string,
  patch: Partial<AgentRuntimeState>,
): Record<string, AgentRuntimeState> {
  return { ...agents, [id]: { ...getAgent(agents, id), ...patch } };
}

export const useAgentRuntimeStore = create<AgentRuntimeStore>((set) => ({
  agents: {},

  setThinking: (agentId, thinking, context) =>
    set((s) => ({
      agents: putAgent(s.agents, agentId, {
        thinking,
        context: thinking ? (context ?? null) : null,
        lastActivity: Date.now(),
      }),
    })),

  addRunningTask: (agentId, task) =>
    set((s) => {
      const agent = getAgent(s.agents, agentId);
      if (agent.runningTasks.some((t) => t.path === task.path)) return s;
      return {
        agents: putAgent(s.agents, agentId, {
          runningTasks: [...agent.runningTasks, task],
          lastActivity: Date.now(),
        }),
      };
    }),

  removeRunningTask: (agentId, taskPath) =>
    set((s) => {
      const agent = getAgent(s.agents, agentId);
      return {
        agents: putAgent(s.agents, agentId, {
          runningTasks: agent.runningTasks.filter((t) => t.path !== taskPath),
          lastActivity: Date.now(),
        }),
      };
    }),

  setRunningTasks: (agentId, tasks) =>
    set((s) => ({
      agents: putAgent(s.agents, agentId, {
        runningTasks: tasks,
        lastActivity: Date.now(),
      }),
    })),

  appendTaskLog: (agentId, taskPath, content) =>
    set((s) => {
      const agent = getAgent(s.agents, agentId);
      return {
        agents: putAgent(s.agents, agentId, {
          taskLogs: {
            ...agent.taskLogs,
            [taskPath]: (agent.taskLogs[taskPath] || "") + content,
          },
        }),
      };
    }),

  clearTaskLog: (agentId, taskPath) =>
    set((s) => {
      const agent = getAgent(s.agents, agentId);
      const { [taskPath]: _, ...rest } = agent.taskLogs;
      return { agents: putAgent(s.agents, agentId, { taskLogs: rest }) };
    }),

  clearAgent: (agentId) =>
    set((s) => ({ agents: putAgent(s.agents, agentId, { ...DEFAULT_STATE }) })),
}));

// ── Selector hooks ──────────────────────────────────────────────────

export function useAgentRuntime(agentId: string): AgentRuntimeState {
  return useAgentRuntimeStore(
    useCallback((s: AgentRuntimeStore) => s.agents[agentId] ?? DEFAULT_STATE, [agentId]),
  );
}

export function useThinkingAgents(): string[] {
  return useAgentRuntimeStore(
    useShallow((s) =>
      Object.entries(s.agents)
        .filter(([, state]) => state.thinking)
        .map(([id]) => id),
    ),
  );
}
