const TOOL_LABELS: Record<string, string> = {
  vault_read: "Reading vault",
  vault_write: "Writing to vault",
  vault_search: "Searching vault",
  vault_list: "Listing vault",
  task_create: "Creating task",
  task_update: "Updating task",
  task_list: "Listing tasks",
  issue_create: "Creating issue",
  issue_update: "Updating issue",
  issue_list: "Listing issues",
  issue_comment: "Adding comment",
  achievement_create: "Recording achievement",
  delegate_task: "Delegating task",
  request_agent: "Requesting agent",
  route_to_agent: "Routing",
  open_huddle: "Starting huddle",
};

interface Props {
  tool: string;
  agentId?: string;
  /** Whether this event is happening live (true) or loaded from history (false). */
  live?: boolean;
}

export function ToolUseBadge({ tool, agentId, live = true }: Props) {
  const label = TOOL_LABELS[tool] || tool.replace(/_/g, " ");

  return (
    <div className="flex items-center gap-2 py-1 text-[11px] text-base-content/60">
      <span className={`w-1.5 h-1.5 rounded-full bg-primary ${live ? "animate-pulse motion-reduce:animate-none" : ""}`} />
      {agentId && (
        <span className="text-base-content/50">{agentId}</span>
      )}
      <span>{label}</span>
    </div>
  );
}
