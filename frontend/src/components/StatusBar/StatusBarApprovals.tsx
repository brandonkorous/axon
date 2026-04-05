import { Link } from "react-router-dom";
import type { Approval } from "../../stores/approvalStore";
import {
    usePendingApprovals,
    useApprove,
    useDecline,
} from "../../hooks/useApprovals";
import { PRIORITY_BADGE } from "../../constants/badges";
import { StatusBarPopover } from "./StatusBarPopover";

function ApprovalItem({ approval }: { approval: Approval }) {
    const approveMutation = useApprove();
    const declineMutation = useDecline();
    const acting = approveMutation.isPending || declineMutation.isPending;

    const handleApprove = async () => {
        await approveMutation.mutateAsync(approval.task_path);
    };

    const handleDecline = async () => {
        await declineMutation.mutateAsync({ taskPath: approval.task_path });
    };

    return (
        <li className="flex flex-row items-center justify-between gap-3 px-3 py-2 hover:bg-base-content/5 rounded-lg">
            <div className="flex-1 min-w-0">
                <div className="flex items-center gap-1.5">
                    {approval.type === "comms_outbound" && (
                        <span className="badge badge-info badge-xs">{approval.channel || "msg"}</span>
                    )}
                    <span className="text-sm font-medium text-base-content truncate">
                        {approval.title}
                    </span>
                </div>
                <div className="flex items-center gap-2 mt-0.5 text-xs text-base-content/60">
                    <span>{approval.delegated_by}</span>
                    <span className={`badge badge-soft badge-xs ${PRIORITY_BADGE[approval.priority] || "badge-ghost"}`}>
                        {approval.priority}
                    </span>
                </div>
            </div>
            <div className="flex gap-1 flex-shrink-0">
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
        </li>
    );
}

export function StatusBarApprovals({ count }: { count: number }) {
    const { data: pendingData } = usePendingApprovals();
    const approvals = (pendingData ?? []) as Approval[];

    return (
        <StatusBarPopover
            label={`${count} pending approvals`}
            width="w-96"

            trigger={
                <>
                    <span
                        className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${count > 0 ? "bg-warning" : "bg-neutral/50"}`}
                    />
                    <span>{count}</span>
                    <span className="hidden sm:inline">
                        {count === 1 ? "Approval" : "Approvals"}
                    </span>
                </>
            }
        >
            <div className="flex items-center justify-between px-3 py-2 border-b border-base-content/10">
                <span className="text-xs font-medium text-base-content">
                    Pending Approvals
                </span>
                <Link to="/approvals" className="text-xs text-primary hover:underline">
                    View all
                </Link>
            </div>

            <ul className="overflow-y-auto flex-1 p-1 space-y-0.5">
                {approvals.length === 0 && (
                    <li className="px-3 py-3 text-xs text-base-content/50 text-center">
                        No pending approvals
                    </li>
                )}
                {approvals.map((approval) => (
                    <ApprovalItem key={approval.task_path} approval={approval} />
                ))}
            </ul>
        </StatusBarPopover>
    );
}
