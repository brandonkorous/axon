import { useAgents } from "../../hooks/useAgents";
import { DEFAULT_AGENT_COLOR } from "../../constants/theme";

interface Props {
  type: "agent_activated" | "agent_result";
  agentId: string;
  taskSummary: string;
  mode?: string;
  status?: string;
  /** Whether this event is happening live (true) or loaded from history (false). */
  live?: boolean;
}

export function AgentActivityBadge({ type, agentId, taskSummary, mode, status, live = true }: Props) {
  const { data: agents = [] } = useAgents();
  const agent = agents.find((a) => a.id === agentId);
  const name = agent?.name || agentId;
  const color = agent?.ui.color || DEFAULT_AGENT_COLOR;

  if (type === "agent_activated") {
    return (
      <div
        className="flex items-center gap-2 py-2 px-3 rounded-lg text-xs border"
        style={{
          backgroundColor: `${color}10`,
          borderColor: `${color}30`,
          color,
        }}
      >
        <span
          className={`w-1.5 h-1.5 rounded-full shrink-0 ${live ? "animate-pulse motion-reduce:animate-none" : ""}`}
          style={{ backgroundColor: color }}
        />
        <span className="font-medium">{name}</span>
        <span className="text-base-content/50">
          working on: {taskSummary}
          {mode === "sync" && " (waiting for result)"}
        </span>
      </div>
    );
  }

  const isSuccess = status === "success" || status === "done";

  return (
    <div
      className="flex items-center gap-2 py-2 px-3 rounded-lg text-xs border"
      style={{
        backgroundColor: isSuccess ? `${color}10` : "oklch(var(--er) / 0.1)",
        borderColor: isSuccess ? `${color}30` : "oklch(var(--er) / 0.2)",
        color: isSuccess ? color : "oklch(var(--er))",
      }}
    >
      {isSuccess ? (
        <svg
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth={2}
          className="w-3.5 h-3.5 shrink-0"
          aria-hidden="true"
        >
          <path d="M5 13l4 4L19 7" />
        </svg>
      ) : (
        <svg
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth={2}
          className="w-3.5 h-3.5 shrink-0"
          aria-hidden="true"
        >
          <path d="M6 18L18 6M6 6l12 12" />
        </svg>
      )}
      <span className="font-medium">{name}</span>
      <span style={{ color: isSuccess ? `${color}99` : undefined }}>
        {isSuccess ? "completed" : "failed"}: {taskSummary}
      </span>
    </div>
  );
}
