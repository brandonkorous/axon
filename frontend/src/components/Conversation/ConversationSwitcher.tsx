import { ConversationMeta } from "../../stores/conversationStore";

interface ConversationSwitcherProps {
  conversations: ConversationMeta[];
  activeId: string;
  onSwitch: (conversationId: string) => void;
  onCreate: () => void;
  onDelete: (conversationId: string) => void;
}

function formatTimeAgo(timestamp: number): string {
  const seconds = Math.floor((Date.now() / 1000 - timestamp));
  if (seconds < 60) return "just now";
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

export function ConversationSwitcher({
  conversations,
  activeId,
  onSwitch,
  onCreate,
  onDelete,
}: ConversationSwitcherProps) {
  const active = conversations.find((c) => c.id === activeId);
  const title = active?.title || "New conversation";

  return (
    <div className="dropdown dropdown-end">
      <div
        tabIndex={0}
        role="button"
        className="btn btn-ghost btn-sm gap-1 text-xs font-normal text-neutral-content hover:text-base-content"
      >
        <span className="max-w-[180px] truncate">{title}</span>
        <svg viewBox="0 0 20 20" fill="currentColor" className="w-3.5 h-3.5 opacity-50">
          <path fillRule="evenodd" d="M5.22 8.22a.75.75 0 0 1 1.06 0L10 11.94l3.72-3.72a.75.75 0 1 1 1.06 1.06l-4.25 4.25a.75.75 0 0 1-1.06 0L5.22 9.28a.75.75 0 0 1 0-1.06Z" clipRule="evenodd" />
        </svg>
      </div>

      <ul
        tabIndex={0}
        className="dropdown-content menu bg-base-200 border border-neutral rounded-lg shadow-lg z-50 w-72 max-h-80 overflow-y-auto p-1"
      >
        <li>
          <button onClick={onCreate} className="text-accent font-medium text-xs">
            + New conversation
          </button>
        </li>

        {conversations.length > 0 && <li className="border-t border-neutral my-1" />}

        {conversations.map((conv) => (
          <li key={conv.id}>
            <div
              className={`flex items-center justify-between gap-2 text-xs ${
                conv.id === activeId ? "bg-base-300" : ""
              }`}
            >
              <button
                className="flex-1 text-left truncate"
                onClick={() => {
                  onSwitch(conv.id);
                  // Close dropdown by blurring
                  (document.activeElement as HTMLElement)?.blur();
                }}
              >
                <span className="block truncate">{conv.title}</span>
                <span className="text-neutral-content text-[10px]">
                  {formatTimeAgo(conv.last_message_at)} · {conv.message_count} msgs
                </span>
              </button>

              {conversations.length > 1 && (
                <button
                  className="btn btn-ghost btn-xs opacity-0 group-hover:opacity-100 hover:text-error"
                  onClick={(e) => {
                    e.stopPropagation();
                    onDelete(conv.id);
                  }}
                  title="Delete conversation"
                >
                  <svg viewBox="0 0 20 20" fill="currentColor" className="w-3 h-3">
                    <path d="M6.28 5.22a.75.75 0 0 0-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 1 0 1.06 1.06L10 11.06l3.72 3.72a.75.75 0 1 0 1.06-1.06L11.06 10l3.72-3.72a.75.75 0 0 0-1.06-1.06L10 8.94 6.28 5.22Z" />
                  </svg>
                </button>
              )}
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
