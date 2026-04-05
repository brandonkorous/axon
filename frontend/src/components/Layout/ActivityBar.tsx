import { usePanelStore, type LeftPanelView } from "../../stores/panelStore";
import { useSettingsStore } from "../../stores/settingsStore";
import { usePendingApprovals } from "../../hooks/useApprovals";

const TOP_ITEMS: { key: LeftPanelView; label: string; icon: React.ReactNode }[] = [
  {
    key: "agents",
    label: "Agents",
    icon: (
      <svg className="w-5 h-5" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="10" cy="7" r="3" />
        <path d="M4 17c0-3.3 2.7-6 6-6s6 2.7 6 6" />
      </svg>
    ),
  },
  {
    key: "search",
    label: "Search",
    icon: (
      <svg className="w-5 h-5" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="8.5" cy="8.5" r="5" />
        <path d="M12.5 12.5L17 17" />
      </svg>
    ),
  },
  {
    key: "nav",
    label: "Navigation",
    icon: (
      <svg className="w-5 h-5" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M3 5h14M3 10h14M3 15h14" />
      </svg>
    ),
  },
  {
    key: "extensions",
    label: "Extensions",
    icon: (
      <svg className="w-5 h-5" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <rect x="3" y="3" width="6" height="6" rx="1" />
        <rect x="11" y="3" width="6" height="6" rx="1" />
        <rect x="3" y="11" width="6" height="6" rx="1" />
        <path d="M14 11v2.5a1 1 0 001 1h0a1 1 0 001-1V11M14 17v-1.5a1 1 0 011-1h0a1 1 0 011 1V17" />
      </svg>
    ),
  },
];

export function ActivityBar() {
  const { leftOpen, leftView, setLeftView } = usePanelStore();
  const openSettings = useSettingsStore((s) => s.open);
  const { data: pendingApprovals } = usePendingApprovals();
  const approvalCount = pendingApprovals?.length ?? 0;

  return (
    <div className="hidden md:flex w-12 bg-base-300 border-r border-base-content/10 flex-col items-center py-2 gap-0.5 shrink-0 select-none">
      {/* Top icons */}
      <div className="flex flex-col items-center gap-0.5 flex-1">
        {TOP_ITEMS.map((item) => (
          <button
            key={item.key}
            onClick={() => setLeftView(item.key)}
            title={item.label}
            className={`w-10 h-10 rounded-lg flex items-center justify-center transition-colors relative ${
              leftOpen && leftView === item.key
                ? "bg-primary/15 text-primary"
                : "text-base-content/50 hover:text-base-content hover:bg-base-content/10"
            }`}
          >
            {item.icon}
            {item.key === "nav" && approvalCount > 0 && (
              <span className="absolute top-1 right-1 w-2 h-2 rounded-full bg-warning" />
            )}
          </button>
        ))}
      </div>

      {/* Bottom icons */}
      <div className="flex flex-col items-center gap-0.5">
        <button
          onClick={() => openSettings()}
          title="Settings"
          className="w-10 h-10 rounded-lg flex items-center justify-center text-base-content/50 hover:text-base-content hover:bg-base-content/10 transition-colors"
        >
          <svg className="w-5 h-5" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="10" cy="10" r="3" />
            <path d="M10 1v2M10 17v2M1 10h2M17 10h2M3.93 3.93l1.41 1.41M14.66 14.66l1.41 1.41M3.93 16.07l1.41-1.41M14.66 5.34l1.41-1.41" />
          </svg>
        </button>
      </div>
    </div>
  );
}
