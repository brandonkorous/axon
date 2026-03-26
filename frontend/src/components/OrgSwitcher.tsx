import { useState } from "react";
import { useOrgStore } from "../stores/orgStore";
import { OrgCreatorModal } from "./OrgCreator/OrgCreatorModal";
import { OrgEditModal } from "./OrgEditModal";

export function OrgSwitcher() {
  const { orgs, activeOrgId, isMultiOrg, setActiveOrg } = useOrgStore();
  const [showCreator, setShowCreator] = useState(false);
  const [showEditor, setShowEditor] = useState(false);

  const activeOrg = orgs.find((o) => o.id === activeOrgId);

  return (
    <>
      <div className="px-3 py-2 border-b border-neutral">
        <label className="block text-[10px] font-semibold text-base-content/60 uppercase tracking-wider mb-1">
          Organization
        </label>
        {orgs.length === 0 ? (
          <button
            onClick={() => setShowCreator(true)}
            className="btn btn-ghost btn-sm w-full justify-start gap-2 text-base-content/60"
          >
            <span>+</span>
            <span>Create an organization</span>
          </button>
        ) : (
          <>
            <div className="flex gap-1.5">
              {isMultiOrg ? (
                <select
                  value={activeOrgId}
                  onChange={(e) => {
                    setActiveOrg(e.target.value);
                    window.location.reload();
                  }}
                  className="select select-sm flex-1"
                >
                  {orgs.map((org) => (
                    <option key={org.id} value={org.id}>
                      {org.name}
                    </option>
                  ))}
                </select>
              ) : (
                <span className="text-sm text-base-content flex-1 truncate py-1">
                  {activeOrg?.name ?? orgs[0]?.name}
                </span>
              )}
              <button
                onClick={() => setShowEditor(true)}
                className="btn btn-ghost btn-sm btn-square"
                aria-label="Edit organization"
              >
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} className="w-3.5 h-3.5">
                  <path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7" />
                  <path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z" />
                </svg>
              </button>
              <button
                onClick={() => setShowCreator(true)}
                className="btn btn-ghost btn-sm btn-square"
                aria-label="Create new organization"
              >
                +
              </button>
            </div>
            {activeOrg?.description && (
              <p className="text-[10px] text-base-content/60 mt-1 truncate">
                {activeOrg.description}
              </p>
            )}
          </>
        )}
      </div>

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
