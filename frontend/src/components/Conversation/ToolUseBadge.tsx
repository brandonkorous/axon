const TOOL_LABELS: Record<string, string> = {
  memory_read: "Reading memory",
  memory_write: "Writing to memory",
  memory_search: "Searching memory",
  memory_list: "Listing memory",
  task_create: "Creating task",
  task_update: "Updating task",
  task_list: "Listing tasks",
  issue_create: "Creating issue",
  issue_update: "Updating issue",
  issue_list: "Listing issues",
  issue_comment: "Adding comment",
  delegate_task: "Delegating task",
  request_agent: "Requesting agent",
  route_to_agent: "Routing",
  open_huddle: "Starting huddle",
  plugins_discover: "Searching plugins",
  plugins_enable: "Enabling plugin",
  plugins_request: "Requesting plugin",
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
