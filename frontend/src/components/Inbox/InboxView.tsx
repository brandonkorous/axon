import { useEffect, useState } from "react";
import { useInboxStore, type InboxItem, type InboxItemType } from "../../stores/inboxStore";
import { useAgentStore } from "../../stores/agentStore";

const TYPE_BADGE: Record<InboxItemType, string> = {
  task_completed: "badge-success",
  plan_ready: "badge-info",
  task_failed: "badge-error",
  plan_declined: "badge-warning",
};

const TYPE_LABEL: Record<InboxItemType, string> = {
  task_completed: "completed",
  plan_ready: "plan ready",
  task_failed: "failed",
  plan_declined: "declined",
};

function InboxRow({
  item,
  isExpanded,
  onToggle,
  onMarkRead,
}: {
  item: InboxItem;
  isExpanded: boolean;
  onToggle: () => void;
  onMarkRead: () => void;
}) {
  const [acting, setActing] = useState(false);

  const handleMarkRead = async (e: React.MouseEvent) => {
    e.stopPropagation();
    setActing(true);
    await onMarkRead();
    setActing(false);
  };

  return (
    <>
      <tr
        onClick={onToggle}
        onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && onToggle()}
        tabIndex={0}
        role="button"
        className={`hover cursor-pointer ${item.status === "pending" ? "font-medium" : "opacity-70"}`}
      >
        <td className="text-sm text-base-content/60">{item.from}</td>
        <td>
          <span className={`badge badge-soft badge-xs ${TYPE_BADGE[item.type] || "badge-ghost"}`}>
            {TYPE_LABEL[item.type] || item.type}
          </span>
        </td>
        <td className="text-sm text-base-content/80 truncate max-w-xs">
          {item.content.slice(0, 80)}
          {item.content.length > 80 ? "..." : ""}
        </td>
        <td className="text-sm text-base-content/60">{item.date}</td>
        <td>
          {item.status === "pending" && (
            <button
              onClick={handleMarkRead}
              disabled={acting}
              className="btn btn-ghost btn-xs"
            >
              {acting ? "..." : "Mark Read"}
            </button>
          )}
          {item.status !== "pending" && (
            <span className="text-xs text-base-content/60">{item.status}</span>
          )}
        </td>
      </tr>
      {isExpanded && (
        <tr>
          <td colSpan={5} className="bg-base-300 p-4">
            <pre className="text-sm text-base-content/80 whitespace-pre-wrap font-sans max-h-64 overflow-y-auto">
              {item.content}
            </pre>
            {item.task_ref && (
              <p className="text-xs text-base-content/60 mt-2">
                Ref: {item.task_ref}
              </p>
            )}
          </td>
        </tr>
      )}
    </>
  );
}

export function InboxView() {
  const { items, loading, fetchAll, markAsRead } = useInboxStore();
  const { agents } = useAgentStore();
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [agentFilter, setAgentFilter] = useState<string>("");

  useEffect(() => {
    fetchAll();
  }, [fetchAll]);

  const filtered = agentFilter
    ? items.filter((i) => i.agent_id === agentFilter)
    : items;

  const pendingCount = items.filter((i) => i.status === "pending").length;
  const agentIds = [...new Set(items.map((i) => i.agent_id))];

  const toggleExpand = (key: string) => {
    setExpandedId((prev) => (prev === key ? null : key));
  };

  return (
    <div className="h-full flex flex-col">
      <div className="flex items-center justify-between px-6 py-4 border-b border-neutral">
        <div className="flex items-center gap-4">
          <h1 className="text-xl font-bold text-base-content">Inbox</h1>
          {pendingCount > 0 && (
            <span className="badge badge-info badge-sm">{pendingCount} pending</span>
          )}
          <div className="flex gap-1">
            <button
              onClick={() => setAgentFilter("")}
              className={`btn btn-xs ${agentFilter === "" ? "btn-primary" : "btn-ghost"}`}
            >
              All
            </button>
            {agentIds.map((id) => {
              const agent = agents.find((a) => a.id === id);
              return (
                <button
                  key={id}
                  onClick={() => setAgentFilter(id)}
                  className={`btn btn-xs ${agentFilter === id ? "btn-primary" : "btn-ghost"}`}
                >
                  {agent?.name || id}
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {loading && items.length === 0 ? (
        <div className="flex-1 flex items-center justify-center">
          <span className="loading loading-spinner loading-md text-primary" />
        </div>
      ) : filtered.length === 0 ? (
        <div className="flex-1 flex items-center justify-center text-base-content/60">
          No inbox items
        </div>
      ) : (
        <div className="flex-1 overflow-y-auto">
          <table className="table table-sm table-pin-rows">
            <caption className="sr-only">Inbox items</caption>
            <thead>
              <tr>
                <th className="w-32">From</th>
                <th className="w-24">Type</th>
                <th>Preview</th>
                <th className="w-28">Date</th>
                <th className="w-24">Status</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((item) => {
                const key = `${item.agent_id}/${item.filename}`;
                return (
                  <InboxRow
                    key={key}
                    item={item}
                    isExpanded={expandedId === key}
                    onToggle={() => toggleExpand(key)}
                    onMarkRead={() => markAsRead(item.agent_id, item.filename)}
                  />
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
