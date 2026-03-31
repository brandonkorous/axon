import { AnimatePresence, motion } from "framer-motion";
import { useToolbeltSidebarStore, SidebarTab } from "../../stores/toolbeltSidebarStore";
import { SidebarPanel } from "./SidebarPanel";

const TABS: { key: SidebarTab; label: string; icon: React.ReactNode }[] = [
  {
    key: "plugins",
    label: "Plugins",
    icon: (
      <svg className="w-5 h-5" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <rect x="3" y="3" width="6" height="6" rx="1" />
        <rect x="11" y="3" width="6" height="6" rx="1" />
        <rect x="3" y="11" width="6" height="6" rx="1" />
        <path d="M14 11v2.5a1 1 0 001 1h0a1 1 0 001-1V11M14 17v-1.5a1 1 0 011-1h0a1 1 0 011 1V17" />
      </svg>
    ),
  },
  {
    key: "skills",
    label: "Skills",
    icon: (
      <svg className="w-5 h-5" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M11 2L5 11h4l-1 7 7-9h-4l1-7z" />
      </svg>
    ),
  },
  {
    key: "sandboxes",
    label: "Sandboxes",
    icon: (
      <svg className="w-5 h-5" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <rect x="3" y="4" width="14" height="12" rx="2" />
        <path d="M6 8l2 2-2 2" />
        <path d="M10 12h4" />
      </svg>
    ),
  },
  {
    key: "comms",
    label: "Communication",
    icon: (
      <svg className="w-5 h-5" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M3 5a2 2 0 012-2h10a2 2 0 012 2v7a2 2 0 01-2 2H8l-4 3v-3a2 2 0 01-1-1.7V5z" />
        <path d="M7 8h6M7 11h4" />
      </svg>
    ),
  },
];

export function ToolbeltSidebar({ agentId }: { agentId: string }) {
  const { isOpen, activeTab, close } = useToolbeltSidebarStore();

  const handleTabClick = (tab: SidebarTab) => {
    const store = useToolbeltSidebarStore.getState();
    if (store.isOpen && store.activeTab === tab) {
      store.close();
    } else {
      store.setTab(tab);
    }
  };

  return (
    <>
      {/* Mobile backdrop */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            className="fixed inset-0 z-30 bg-black/50 md:hidden"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={close}
          />
        )}
      </AnimatePresence>

      <div className="flex h-full">
        {/* Panel */}
        <AnimatePresence>
          {isOpen && (
            <motion.div
              className="h-full bg-base-200 border-l border-neutral overflow-hidden fixed right-12 inset-y-0 z-40 md:static md:z-auto"
              initial={{ width: 0, opacity: 0 }}
              animate={{ width: 320, opacity: 1 }}
              exit={{ width: 0, opacity: 0 }}
              transition={{ type: "spring", damping: 30, stiffness: 300 }}
            >
              <SidebarPanel agentId={agentId} />
            </motion.div>
          )}
        </AnimatePresence>

        {/* Activity Bar */}
        <div className="hidden md:flex w-12 bg-base-300 border-l border-neutral flex-col items-center py-3 gap-1 shrink-0">
          {TABS.map((tab) => (
            <button
              key={tab.key}
              onClick={() => handleTabClick(tab.key)}
              title={tab.label}
              className={`w-9 h-9 rounded-lg flex items-center justify-center transition-colors ${
                isOpen && activeTab === tab.key
                  ? "bg-primary/15 text-primary"
                  : "text-base-content/50 hover:text-base-content hover:bg-base-content/10"
              }`}
            >
              {tab.icon}
            </button>
          ))}
        </div>
      </div>
    </>
  );
}
