import { useEffect, useRef, useState } from "react";
import type { Approval, CommsPayload } from "../../stores/approvalStore";
import { useApprovalStore } from "../../stores/approvalStore";
import { PRIORITY_BADGE } from "../../constants/badges";

function CommsPreview({ channel, payload: raw }: { channel?: string; payload: string }) {
  let parsed: CommsPayload = {};
  try {
    parsed = JSON.parse(raw);
  } catch {
    return <p className="text-xs text-error">Invalid message payload</p>;
  }

  if (channel === "email") {
    return (
      <div className="space-y-3">
        <h4 className="text-sm font-semibold text-base-content/60">Outbound Email</h4>
        <div className="bg-base-100 rounded p-4 space-y-2 text-sm">
          <div><span className="text-base-content/60">To:</span> <span className="text-base-content">{parsed.to}</span></div>
          {parsed.cc && <div><span className="text-base-content/60">CC:</span> <span className="text-base-content">{parsed.cc}</span></div>}
          <div><span className="text-base-content/60">Subject:</span> <span className="text-base-content font-medium">{parsed.subject}</span></div>
          <div className="border-t border-neutral pt-2 mt-2">
            <pre className="text-xs text-base-content/80 whitespace-pre-wrap">{parsed.body}</pre>
          </div>
        </div>
      </div>
    );
  }

  if (channel === "discord") {
    return (
      <div className="space-y-3">
        <h4 className="text-sm font-semibold text-base-content/60">Outbound Discord Message</h4>
        <div className="bg-base-100 rounded p-4 space-y-2 text-sm">
          <div>
            <span className="text-base-content/60">{parsed.is_dm ? "DM to:" : "Channel:"}</span>{" "}
            <span className="text-base-content font-mono">{parsed.target}</span>
          </div>
          <div className="border-t border-neutral pt-2 mt-2">
            <pre className="text-xs text-base-content/80 whitespace-pre-wrap">{parsed.content}</pre>
          </div>
        </div>
      </div>
    );
  }

  return <p className="text-xs text-base-content/60">Unknown channel: {channel}</p>;
}

interface ApprovalDetailModalProps {
  approval: Approval;
  onClose: () => void;
}

export function ApprovalDetailModal({ approval, onClose }: ApprovalDetailModalProps) {
  const { approve, decline } = useApprovalStore();
  const dialogRef = useRef<HTMLDialogElement>(null);
  const [acting, setActing] = useState(false);
  const [showDecline, setShowDecline] = useState(false);
  const [declineReason, setDeclineReason] = useState("");

  useEffect(() => {
    dialogRef.current?.showModal();
  }, []);

  const handleApprove = async () => {
    setActing(true);
    await approve(approval.task_path);
    setActing(false);
    onClose();
  };

  const handleDecline = async () => {
    setActing(true);
    await decline(approval.task_path, declineReason || undefined);
    setActing(false);
    onClose();
  };

  return (
    <dialog ref={dialogRef} className="modal" onClose={onClose}>
      <div className="modal-box max-w-2xl max-h-[80vh] flex flex-col">
        <div className="flex items-start justify-between mb-4">
          <div>
            <h3 className="text-lg font-bold text-base-content">{approval.title}</h3>
            <div className="flex items-center gap-2 mt-1">
              <span className={`badge badge-soft badge-xs ${PRIORITY_BADGE[approval.priority] || "badge-ghost"}`}>
                {approval.priority}
              </span>
              <span className="text-xs text-base-content/60">
                {approval.delegated_by} → {approval.assignee}
              </span>
              <span className="text-xs text-base-content/60">
                {new Date(approval.created_at).toLocaleDateString()}
              </span>
            </div>
          </div>
          <form method="dialog">
            <button className="btn btn-ghost btn-sm btn-square" aria-label="Close">X</button>
          </form>
        </div>

        <div className="flex-1 overflow-y-auto space-y-4">
          {approval.type === "comms_outbound" && approval.comms_payload ? (
            <CommsPreview channel={approval.channel} payload={approval.comms_payload} />
          ) : (
            <>
              {approval.plan_content && (
                <div>
                  <h4 className="text-sm font-semibold text-base-content/60 mb-2">Plan</h4>
                  <pre className="p-4 bg-base-100 rounded text-xs text-base-content/80 overflow-x-auto max-h-96 overflow-y-auto whitespace-pre-wrap">
                    {approval.plan_content}
                  </pre>
                </div>
              )}

              {approval.files_affected.length > 0 && (
                <div>
                  <h4 className="text-sm font-semibold text-base-content/60 mb-2">
                    Files Affected ({approval.files_affected.length})
                  </h4>
                  <ul className="space-y-1">
                    {approval.files_affected.map((file) => (
                      <li key={file} className="text-xs font-mono text-base-content/70">{file}</li>
                    ))}
                  </ul>
                </div>
              )}
            </>
          )}
        </div>

        <div className="pt-4 border-t border-neutral mt-4">
          {showDecline ? (
            <div className="flex gap-2">
              <input
                value={declineReason}
                onChange={(e) => setDeclineReason(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleDecline()}
                placeholder="Reason (optional)"
                aria-label="Decline reason"
                className="input input-sm flex-1"
                autoFocus
              />
              <button onClick={handleDecline} disabled={acting} className="btn btn-error btn-sm">
                {acting ? "..." : "Confirm Decline"}
              </button>
              <button onClick={() => setShowDecline(false)} className="btn btn-ghost btn-sm">
                Cancel
              </button>
            </div>
          ) : (
            <div className="flex gap-2 justify-end">
              <button onClick={() => setShowDecline(true)} disabled={acting} className="btn btn-error btn-soft btn-sm">
                Decline
              </button>
              <button onClick={handleApprove} disabled={acting} className="btn btn-success btn-sm">
                {acting ? "..." : "Approve"}
              </button>
            </div>
          )}
        </div>
      </div>
      <form method="dialog" className="modal-backdrop"><button>close</button></form>
    </dialog>
  );
}
