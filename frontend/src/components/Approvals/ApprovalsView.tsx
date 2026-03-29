import { useEffect, useState } from "react";
import { useApprovalStore, type Approval, type ApprovalHistoryItem } from "../../stores/approvalStore";
import { PRIORITY_BADGE } from "../../constants/badges";
import { ApprovalDetailModal } from "./ApprovalDetailModal";

const STATUS_BADGE: Record<string, string> = {
  approved: "badge-success",
  declined: "badge-error",
  send_failed: "badge-warning",
};

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
        <div className="flex items-center gap-2">
          {approval.type === "comms_outbound" && (
            <span className="badge badge-info badge-xs">{approval.channel || "msg"}</span>
          )}
          <span className="text-sm text-base-content font-medium">{approval.title}</span>
        </div>
      </td>
      <td className="text-sm text-base-content/60">{approval.delegated_by}</td>
      <td className="text-sm text-base-content/60">{approval.assignee}</td>
      <td>
        <span className={`badge badge-soft badge-xs ${PRIORITY_BADGE[approval.priority] || "badge-ghost"}`}>
          {approval.priority}
        </span>
      </td>
      <td className="text-sm text-base-content/60">
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

function HistoryRow({ item }: { item: ApprovalHistoryItem }) {
  return (
    <tr>
      <td>
        <div className="flex items-center gap-2">
          {item.type === "comms_outbound" && (
            <span className="badge badge-info badge-xs">{item.channel || "msg"}</span>
          )}
          <span className="text-sm text-base-content font-medium">{item.title}</span>
        </div>
      </td>
      <td>
        <span className={`badge badge-soft badge-xs ${STATUS_BADGE[item.status] || "badge-ghost"}`}>
          {item.status === "send_failed" ? "failed" : item.status}
        </span>
      </td>
      <td className="text-sm text-base-content/60">{item.created_by}</td>
      <td className="text-sm text-base-content/60">
        {new Date(item.approved_at || item.updated_at).toLocaleDateString()}
      </td>
      <td className="text-sm text-base-content/60 max-w-xs truncate">
        {item.decline_reason || item.send_result || ""}
      </td>
    </tr>
  );
}

export function ApprovalsView() {
  const { approvals, loading, fetchPending, history, historyLoading, fetchHistory } = useApprovalStore();
  const [selected, setSelected] = useState<Approval | null>(null);
  const [tab, setTab] = useState<"pending" | "history">("pending");

  useEffect(() => {
    fetchPending();
  }, [fetchPending]);

  useEffect(() => {
    if (tab === "history" && history.length === 0 && !historyLoading) {
      fetchHistory();
    }
  }, [tab, history.length, historyLoading, fetchHistory]);

  return (
    <div className="h-full flex flex-col">
      <div className="flex items-center justify-between px-6 py-4 border-b border-neutral">
        <div className="flex items-center gap-3">
          <h1 className="text-xl font-bold text-base-content">Approvals</h1>
          {approvals.length > 0 && (
            <span className="badge badge-warning badge-sm">{approvals.length} pending</span>
          )}
        </div>
        <div role="tablist" className="tabs tabs-box tabs-sm">
          <button
            role="tab"
            className={`tab ${tab === "pending" ? "tab-active" : ""}`}
            onClick={() => setTab("pending")}
          >
            Pending
          </button>
          <button
            role="tab"
            className={`tab ${tab === "history" ? "tab-active" : ""}`}
            onClick={() => setTab("history")}
          >
            History
          </button>
        </div>
      </div>

      {tab === "pending" && (
        <>
          {loading && approvals.length === 0 ? (
            <div className="flex-1 flex items-center justify-center">
              <span className="loading loading-spinner loading-md text-primary" />
            </div>
          ) : approvals.length === 0 ? (
            <div className="flex-1 flex items-center justify-center text-base-content/60">
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
        </>
      )}

      {tab === "history" && (
        <>
          {historyLoading && history.length === 0 ? (
            <div className="flex-1 flex items-center justify-center">
              <span className="loading loading-spinner loading-md text-primary" />
            </div>
          ) : history.length === 0 ? (
            <div className="flex-1 flex items-center justify-center text-base-content/60">
              No approval history
            </div>
          ) : (
            <div className="flex-1 overflow-y-auto">
              <table className="table table-sm table-pin-rows">
                <caption className="sr-only">Approval history</caption>
                <thead>
                  <tr>
                    <th>Title</th>
                    <th className="w-24">Status</th>
                    <th className="w-28">Agent</th>
                    <th className="w-28">Date</th>
                    <th>Detail</th>
                  </tr>
                </thead>
                <tbody>
                  {history.map((item) => (
                    <HistoryRow key={item.task_path} item={item} />
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
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
