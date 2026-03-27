import { useEffect, useRef } from "react";
import { SettingsTab, useSettingsStore } from "../../stores/settingsStore";
import { GeneralTab } from "./GeneralTab";
import { OrganizationTab } from "./OrganizationTab";
import { ModelsTab } from "./ModelsTab";
import { AgentsTab } from "./AgentsTab";
import { VoiceTab } from "./VoiceTab";
import { CredentialsTab } from "./CredentialsTab";
import { ExtensionsTab } from "./ExtensionsTab";

const TABS: { id: SettingsTab; label: string }[] = [
  { id: "general", label: "General" },
  { id: "organization", label: "Organization" },
  { id: "models", label: "Models" },
  { id: "agents", label: "Agents" },
  { id: "voice", label: "Voice" },
  { id: "credentials", label: "Credentials" },
  { id: "extensions", label: "Extensions" },
];

const TAB_COMPONENTS: Record<SettingsTab, React.FC> = {
  general: GeneralTab,
  organization: OrganizationTab,
  models: ModelsTab,
  agents: AgentsTab,
  voice: VoiceTab,
  credentials: CredentialsTab,
  extensions: ExtensionsTab,
};

export function SettingsModal() {
  const isOpen = useSettingsStore((s) => s.isOpen);
  const activeTab = useSettingsStore((s) => s.activeTab);
  const close = useSettingsStore((s) => s.close);
  const setTab = useSettingsStore((s) => s.setTab);
  const dialogRef = useRef<HTMLDialogElement>(null);

  useEffect(() => {
    if (isOpen) {
      dialogRef.current?.showModal();
    } else {
      dialogRef.current?.close();
    }
  }, [isOpen]);

  const ActiveComponent = TAB_COMPONENTS[activeTab];

  return (
    <dialog ref={dialogRef} className="modal" onClose={close}>
      <div className="modal-box max-w-3xl h-[80vh] p-0 flex bg-base-200 border border-neutral">
        {/* Tab sidebar */}
        <nav className="w-44 shrink-0 border-r border-neutral bg-base-300/50 py-4 px-2 overflow-y-auto">
          <h3 className="text-xs font-semibold text-base-content/60 uppercase tracking-wider px-3 mb-2">
            Settings
          </h3>
          <ul className="menu menu-sm w-full gap-0.5">
            {TABS.map((tab) => (
              <li key={tab.id}>
                <button
                  className={activeTab === tab.id ? "menu-active" : ""}
                  onClick={() => setTab(tab.id)}
                >
                  {tab.label}
                </button>
              </li>
            ))}
          </ul>
        </nav>

        {/* Content area */}
        <div className="flex-1 flex flex-col min-w-0">
          <div className="flex items-center justify-between px-5 py-3 border-b border-neutral">
            <h3 className="text-sm font-semibold">
              {TABS.find((t) => t.id === activeTab)?.label}
            </h3>
            <form method="dialog">
              <button className="btn btn-ghost btn-sm btn-square" aria-label="Close">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} className="w-4 h-4">
                  <path d="M18 6L6 18M6 6l12 12" />
                </svg>
              </button>
            </form>
          </div>
          <div className="flex-1 overflow-y-auto px-5 py-4">
            <ActiveComponent />
          </div>
        </div>
      </div>

      <form method="dialog" className="modal-backdrop">
        <button aria-label="Close"><span className="sr-only">close</span></button>
      </form>
    </dialog>
  );
}
