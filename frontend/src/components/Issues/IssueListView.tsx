import { useEffect, useRef, useState } from "react";
import { useIssues, useCreateIssue, useUpdateIssue, useAddComment, type Issue } from "../../hooks/useIssues";
import { useAgents } from "../../hooks/useAgents";
import { PRIORITY_BADGE, STATUS_BADGE } from "../../constants/badges";


function IssueRow({
  issue,
  onSelect,
}: {
  issue: Issue;
  onSelect: (issue: Issue) => void;
}) {
  return (
    <tr
      onClick={() => onSelect(issue)}
      onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && onSelect(issue)}
      tabIndex={0}
      role="button"
      className="hover cursor-pointer"
    >
      <td className="text-base-content/60 text-sm">#{issue.id}</td>
      <td>
        <div className="flex items-center gap-2">
          <span className="text-sm text-base-content font-medium">{issue.name}</span>
          {issue.labels?.map((label) => (
            <span key={label} className="badge badge-soft badge-accent badge-xs">
              {label}
            </span>
          ))}
        </div>
      </td>
      <td>
        <span className={`badge badge-soft badge-xs ${STATUS_BADGE[issue.status] || "badge-ghost"}`}>
          {issue.status.replace("_", " ")}
        </span>
      </td>
      <td>
        <span className={`text-xs font-bold uppercase ${PRIORITY_BADGE[issue.priority] || "text-base-content/60"}`}>
          {issue.priority}
        </span>
      </td>
      <td className="text-sm text-base-content/60">{issue.assignee || "Unassigned"}</td>
      <td className="text-sm text-base-content/60">{issue.comment_count || 0}</td>
    </tr>
  );
}

function IssueDetail({
  issue,
  onClose,
  onStatusChange,
}: {
  issue: Issue;
  onClose: () => void;
  onStatusChange: (status: string) => void;
}) {
  const addCommentMutation = useAddComment();
  const [comment, setComment] = useState("");
  const [comments, setComments] = useState(issue.comments || []);
  const dialogRef = useRef<HTMLDialogElement>(null);

  useEffect(() => {
    dialogRef.current?.showModal();
  }, []);

  const handleComment = async () => {
    if (!comment.trim()) return;
    await addCommentMutation.mutateAsync({ issueId: issue.id, content: comment });
    setComments([
      ...comments,
      { author: "user", type: "comment", created_at: new Date().toISOString(), body: comment },
    ]);
    setComment("");
  };

  return (
    <dialog ref={dialogRef} className="modal" onClose={onClose}>
      <div className="modal-box max-w-2xl max-h-[80vh] flex flex-col">
        <div className="flex items-start justify-between mb-4">
          <div>
            <span className="text-base-content/60 text-sm">#{issue.id}</span>
            <h3 className="text-lg font-bold text-base-content">{issue.name}</h3>
            <div className="flex items-center gap-2 mt-1">
              <span className={`badge badge-soft badge-xs ${STATUS_BADGE[issue.status] || "badge-ghost"}`}>
                {issue.status.replace("_", " ")}
              </span>
              <span className="text-xs text-base-content/60">
                by {issue.created_by} on {new Date(issue.created_at).toLocaleDateString()}
              </span>
            </div>
          </div>
          <form method="dialog">
            <button className="btn btn-ghost btn-sm btn-square" aria-label="Close">X</button>
          </form>
        </div>

        <div className="flex-1 overflow-y-auto space-y-4">
          <div className="prose prose-sm max-w-none">
            <p className="text-base-content/80 text-sm whitespace-pre-wrap">{issue.body}</p>
          </div>

          <div className="flex gap-2">
            {(["open", "in_progress", "resolved", "closed"] as const)
              .filter((s) => s !== issue.status)
              .map((s) => (
                <button
                  key={s}
                  onClick={() => onStatusChange(s)}
                  className="btn btn-ghost btn-xs"
                >
                  {s.replace("_", " ")}
                </button>
              ))}
          </div>

          <div>
            <h4 className="text-sm font-semibold text-base-content/60 mb-2">
              Comments ({comments.length})
            </h4>
            <div className="space-y-2">
              {comments.map((c, i) => (
                <div key={i} className="card bg-base-300 border border-secondary">
                  <div className="card-body p-3">
                    <div className="flex justify-between text-xs text-base-content/60 mb-1">
                      <span>{c.author}</span>
                      <span>{new Date(c.created_at).toLocaleString()}</span>
                    </div>
                    <p className="text-sm text-base-content/80 whitespace-pre-wrap">{c.body}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="pt-4 border-t border-neutral mt-4">
          <div className="flex gap-2">
            <input
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleComment()}
              placeholder="Add a comment..."
              aria-label="Add a comment"
              className="input input-sm flex-1"
            />
            <button
              onClick={handleComment}
              disabled={!comment.trim()}
              className="btn btn-primary btn-sm"
            >
              Post
            </button>
          </div>
        </div>
      </div>
      <form method="dialog" className="modal-backdrop"><button>close</button></form>
    </dialog>
  );
}

function CreateIssueModal({
  onClose,
  onCreate,
}: {
  onClose: () => void;
  onCreate: (data: {
    title: string;
    description: string;
    assignee: string;
    priority: string;
    labels: string[];
  }) => void;
}) {
  const { data: agents = [] } = useAgents();
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [assignee, setAssignee] = useState("");
  const [priority, setPriority] = useState("p2");
  const [labelsStr, setLabelsStr] = useState("");
  const dialogRef = useRef<HTMLDialogElement>(null);

  useEffect(() => {
    dialogRef.current?.showModal();
  }, []);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) return;
    const labels = labelsStr.split(",").map((l) => l.trim()).filter(Boolean);
    onCreate({ title, description, assignee, priority, labels });
    onClose();
  };

  return (
    <dialog ref={dialogRef} className="modal" onClose={onClose}>
      <div className="modal-box">
        <h3 className="text-lg font-bold mb-4">Create Issue</h3>
        <form onSubmit={handleSubmit} className="space-y-3">
          <input
            autoFocus
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Issue title"
            aria-label="Issue title"
            className="input input-sm w-full"
          />
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Description"
            aria-label="Issue description"
            rows={4}
            className="textarea textarea-sm w-full resize-none"
          />
          <div className="flex gap-3">
            <select
              value={assignee}
              onChange={(e) => setAssignee(e.target.value)}
              aria-label="Assignee"
              className="select select-sm flex-1"
            >
              <option value="">Unassigned</option>
              {agents
                .filter((a) => a.id !== "axon")
                .map((a) => (
                  <option key={a.id} value={a.id}>{a.name}</option>
                ))}
            </select>
            <select
              value={priority}
              onChange={(e) => setPriority(e.target.value)}
              aria-label="Priority"
              className="select select-sm w-24"
            >
              <option value="p0">P0</option>
              <option value="p1">P1</option>
              <option value="p2">P2</option>
              <option value="p3">P3</option>
            </select>
          </div>
          <input
            value={labelsStr}
            onChange={(e) => setLabelsStr(e.target.value)}
            placeholder="Labels (comma-separated)"
            aria-label="Labels"
            className="input input-sm w-full"
          />
          <div className="modal-action">
            <button type="button" onClick={onClose} className="btn btn-ghost btn-sm">Cancel</button>
            <button type="submit" disabled={!title.trim()} className="btn btn-primary btn-sm">Create</button>
          </div>
        </form>
      </div>
      <form method="dialog" className="modal-backdrop"><button>close</button></form>
    </dialog>
  );
}

export function IssueListView() {
  const { data: issues = [], isLoading: loading, isError: error, refetch: fetchIssues } =
    useIssues();
  const createIssueMutation = useCreateIssue();
  const updateIssueMutation = useUpdateIssue();
  const [selected, setSelected] = useState<Issue | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [statusFilter, setStatusFilter] = useState<string>("");

  const filtered = statusFilter
    ? issues.filter((i) => i.status === statusFilter)
    : issues;

  const handleStatusChange = (status: string) => {
    if (selected) {
      updateIssueMutation.mutate({ path: selected.path, data: { status } });
      setSelected({ ...selected, status: status as Issue["status"] });
    }
  };

  return (
    <div className="h-full flex flex-col">
      <div className="flex items-center justify-between px-6 py-4 border-b border-neutral">
        <div className="flex items-center gap-4">
          <h1 className="text-xl font-bold text-base-content">Issues</h1>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            aria-label="Filter by status"
            className="select select-xs"
          >
            <option value="">All statuses</option>
            <option value="open">Open</option>
            <option value="in_progress">In Progress</option>
            <option value="resolved">Resolved</option>
            <option value="closed">Closed</option>
          </select>
        </div>
        <button onClick={() => setShowCreate(true)} className="btn btn-primary btn-sm">
          + New Issue
        </button>
      </div>

      {loading ? (
        <div className="flex-1 flex items-center justify-center">
          <span className="loading loading-spinner loading-md text-primary" />
        </div>
      ) : error ? (
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <p className="text-sm text-error mb-2">Issues aren't loading right now. Try refreshing the page.</p>
            <button onClick={() => fetchIssues()} className="link link-accent text-xs">Try again</button>
          </div>
        </div>
      ) : filtered.length === 0 ? (
        <div className="flex-1 flex items-center justify-center text-base-content/60">
          {statusFilter ? "No issues match this filter" : "No issues yet. Create one to get started."}
        </div>
      ) : (
        <div className="flex-1 overflow-y-auto">
          <table className="table table-sm table-pin-rows">
            <caption className="sr-only">Issue list</caption>
            <thead>
              <tr>
                <th className="w-16">#</th>
                <th>Title</th>
                <th className="w-28">Status</th>
                <th className="w-16">Priority</th>
                <th className="w-28">Assignee</th>
                <th className="w-16">Comments</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((issue) => (
                <IssueRow key={issue.path} issue={issue} onSelect={setSelected} />
              ))}
            </tbody>
          </table>
        </div>
      )}

      {selected && (
        <IssueDetail
          issue={selected}
          onClose={() => setSelected(null)}
          onStatusChange={handleStatusChange}
        />
      )}

      {showCreate && (
        <CreateIssueModal
          onClose={() => setShowCreate(false)}
          onCreate={(data) => createIssueMutation.mutate(data)}
        />
      )}
    </div>
  );
}
