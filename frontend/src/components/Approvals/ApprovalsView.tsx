import { useEffect, useState } from "react";
import { useApprovalStore, type Approval } from "../../stores/approvalStore";
import { PRIORITY_BADGE } from "../../constants/badges";
import { ApprovalDetailModal } from "./ApprovalDetailModal";

function ApprovalRow({
  approval,
  onSelect,
}: {
  approval: Approval;
  onSelect: (a: Approval) => void;
}) {
  const { approve, decline } = useApprovalStore();
  const [acting, setActing] = useState(false);

  const handleApprove = async (e: React.MouseEvent) => {
    e.stopPropagation();
    setActing(true);
    await approve(approval.task_path);
    setActing(false);
  };

  const handleDecline = async (e: React.MouseEvent) => {
    e.stopPropagation();
    setActing(true);
    await decline(approval.task_path);
    setActing(false);
  };

  return (
    <tr
      onClick={() => onSelect(approval)}
      onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && onSelect(approval)}
      tabIndex={0}
      role="button"
      className="hover cursor-pointer"
    >
      <td>
        <span className="text-sm text-base-content font-medium">{approval.title}</span>
      </td>
      <td className="text-sm text-neutral-content">{approval.delegated_by}</td>
      <td className="text-sm text-neutral-content">{approval.assignee}</td>
      <td>
        <span className={`badge badge-soft badge-xs ${PRIORITY_BADGE[approval.priority] || "badge-ghost"}`}>
          {approval.priority}
        </span>
      </td>
      <td className="text-sm text-neutral-content">
        {new Date(approval.created_at).toLocaleDateString()}
      </td>
      <td>
        <div className="flex gap-1" onClick={(e) => e.stopPropagation()}>
          <button
            onClick={handleApprove}
            disabled={acting}
            className="btn btn-success btn-xs"
          >
            {acting ? "..." : "Approve"}
          </button>
          <button
            onClick={handleDecline}
            disabled={acting}
            className="btn btn-error btn-soft btn-xs"
          >
            {acting ? "..." : "Decline"}
          </button>
        </div>
      </td>
    </tr>
  );
}

export function ApprovalsView() {
  const { approvals, loading, fetchPending } = useApprovalStore();
  const [selected, setSelected] = useState<Approval | null>(null);

  useEffect(() => {
    fetchPending();
  }, [fetchPending]);

  return (
    <div className="h-full flex flex-col">
      <div className="flex items-center justify-between px-6 py-4 border-b border-neutral">
        <div className="flex items-center gap-3">
          <h1 className="text-xl font-bold text-base-content">Approvals</h1>
          {approvals.length > 0 && (
            <span className="badge badge-warning badge-sm">{approvals.length} pending</span>
          )}
        </div>
      </div>

      {loading && approvals.length === 0 ? (
        <div className="flex-1 flex items-center justify-center">
          <span className="loading loading-spinner loading-md text-primary" />
        </div>
      ) : approvals.length === 0 ? (
        <div className="flex-1 flex items-center justify-center text-neutral-content">
          No pending approvals
        </div>
      ) : (
        <div className="flex-1 overflow-y-auto">
          <table className="table table-sm table-pin-rows">
            <caption className="sr-only">Pending approvals</caption>
            <thead>
              <tr>
                <th>Title</th>
                <th className="w-28">From</th>
                <th className="w-28">Assignee</th>
                <th className="w-16">Pri</th>
                <th className="w-28">Created</th>
                <th className="w-40">Actions</th>
              </tr>
            </thead>
            <tbody>
              {approvals.map((approval) => (
                <ApprovalRow
                  key={approval.task_path}
                  approval={approval}
                  onSelect={setSelected}
                />
              ))}
            </tbody>
          </table>
        </div>
      )}

      {selected && (
        <ApprovalDetailModal
          approval={selected}
          onClose={() => setSelected(null)}
        />
      )}
    </div>
  );
}
