import { useState } from "react";
import { useOrgStore } from "../../stores/orgStore";
import { useOrgs } from "../../hooks/useOrgs";
import { OrgCreatorModal } from "../OrgCreator/OrgCreatorModal";
import { OrgEditModal } from "../OrgEditModal";
import { StatusBarPopover } from "./StatusBarPopover";

export function StatusBarOrg() {
  const { activeOrgId, setActiveOrg } = useOrgStore();
  const { data: orgs = [] } = useOrgs();
  const [showCreator, setShowCreator] = useState(false);
  const [showEditor, setShowEditor] = useState(false);

  const activeOrg = orgs.find((o) => o.id === activeOrgId);
  const displayName = activeOrg?.name ?? orgs[0]?.name ?? "No org";

  return (
    <>
      <StatusBarPopover
        label={`Organization: ${displayName}`}
        width="w-64"
        trigger={
          <>
            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth={2}
              className="w-3.5 h-3.5 flex-shrink-0"
            >
              <path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
              <polyline points="9 22 9 12 15 12 15 22" />
            </svg>
            <span className="truncate max-w-[120px]">{displayName}</span>
          </>
        }
      >
        {/* Header */}
        <div className="px-3 py-2 border-b border-base-content/10">
          <span className="text-[10px] font-semibold text-base-content/60 uppercase tracking-wider">
            Organization
          </span>
        </div>

        {orgs.length === 0 ? (
          <div className="p-2">
            <button
              onClick={() => setShowCreator(true)}
              className="btn btn-ghost btn-sm w-full justify-start gap-2 text-base-content/60"
            >
              <span>+</span>
              <span>Create an organization</span>
            </button>
          </div>
        ) : (
          <>
            {/* Org list */}
            <ul className="overflow-y-auto max-h-48 p-1 space-y-0.5">
              {orgs.map((org) => {
                const isActive = org.id === activeOrgId;
                return (
                  <li key={org.id}>
                    <button
                      onClick={() => {
                        if (!isActive) {
                          setActiveOrg(org.id);
                          window.location.reload();
                        }
                      }}
                      className={`w-full text-left px-3 py-1.5 rounded-lg text-sm transition-colors flex items-center gap-2 ${
                        isActive
                          ? "bg-primary/10 text-primary font-medium"
                          : "hover:bg-base-300 text-base-content"
                      }`}
                    >
                      <span className="truncate flex-1">{org.name}</span>
                      {isActive && (
                        <svg
                          viewBox="0 0 24 24"
                          fill="none"
                          stroke="currentColor"
                          strokeWidth={2.5}
                          className="w-3.5 h-3.5 flex-shrink-0"
                        >
                          <polyline points="20 6 9 17 4 12" />
                        </svg>
                      )}
                    </button>
                  </li>
                );
              })}
            </ul>

            {/* Actions */}
            <div className="border-t border-base-content/10 p-1 flex gap-1">
              <button
                onClick={() => setShowEditor(true)}
                className="btn btn-ghost btn-xs flex-1 gap-1.5"
              >
                <svg
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth={2}
                  className="w-3 h-3"
                >
                  <path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7" />
                  <path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z" />
                </svg>
                Edit
              </button>
              <button
                onClick={() => setShowCreator(true)}
                className="btn btn-ghost btn-xs flex-1 gap-1.5"
              >
                <svg
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth={2}
                  className="w-3 h-3"
                >
                  <line x1="12" y1="5" x2="12" y2="19" />
                  <line x1="5" y1="12" x2="19" y2="12" />
                </svg>
                New
              </button>
            </div>
          </>
        )}
      </StatusBarPopover>

      <OrgCreatorModal
        isOpen={showCreator}
        onClose={() => setShowCreator(false)}
      />

      {activeOrg && (
        <OrgEditModal
          isOpen={showEditor}
          onClose={() => setShowEditor(false)}
          org={activeOrg}
        />
      )}
    </>
  );
}
