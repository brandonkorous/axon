import { useState } from "react";
import { useOrgStore } from "../stores/orgStore";
import { OrgCreatorModal } from "./OrgCreator/OrgCreatorModal";

export function OrgSwitcher() {
  const { orgs, activeOrgId, isMultiOrg, setActiveOrg } = useOrgStore();
  const [showCreator, setShowCreator] = useState(false);

  const activeOrg = orgs.find((o) => o.id === activeOrgId);

  return (
    <>
      <div className="px-3 py-2 border-b border-neutral">
        <label className="block text-[10px] font-semibold text-neutral-content uppercase tracking-wider mb-1">
          Organization
        </label>
        {orgs.length === 0 ? (
          <button
            onClick={() => setShowCreator(true)}
            className="btn btn-ghost btn-sm w-full justify-start gap-2 text-neutral-content"
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
                onClick={() => setShowCreator(true)}
                className="btn btn-ghost btn-sm btn-square"
                aria-label="Create new organization"
              >
                +
              </button>
            </div>
            {activeOrg?.description && (
              <p className="text-[10px] text-neutral-content mt-1 truncate">
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
    </>
  );
}
