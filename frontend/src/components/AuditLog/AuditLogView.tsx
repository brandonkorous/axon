import { useEffect, useState } from "react";
import { orgApiPath } from "../../stores/orgStore";

interface AuditEntry {
  timestamp: string;
  agent_id: string;
  action: string;
  tool: string;
  conversation_id: string;
  org_id: string;
  path: string;
  body: string;
}

interface AuditResponse {
  entries: AuditEntry[];
  total: number;
  limit: number;
  offset: number;
}

const ACTION_COLORS: Record<string, string> = {
  vault_read: "text-info",
  vault_write: "text-success",
  vault_search: "text-info",
  vault_list: "text-info",
  vault_backlinks: "text-info",
  task_create: "text-accent",
  task_update: "text-accent",
  task_list: "text-accent",
  issue_create: "text-warning",
  issue_update: "text-warning",
  issue_comment: "text-warning",
  issue_list: "text-warning",
  delegate_task: "text-warning",
  request_agent: "text-error",
};

export function AuditLogView() {
  const [data, setData] = useState<AuditResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [agentFilter, setAgentFilter] = useState("");
  const [actionFilter, setActionFilter] = useState("");
  const [expanded, setExpanded] = useState<string | null>(null);
  const [page, setPage] = useState(0);
  const PAGE_SIZE = 50;

  useEffect(() => {
    setLoading(true);
    setError(false);
    const params = new URLSearchParams();
    if (agentFilter) params.set("agent_id", agentFilter);
    if (actionFilter) params.set("action", actionFilter);
    params.set("limit", String(PAGE_SIZE));
    params.set("offset", String(page * PAGE_SIZE));
    const qs = params.toString();

    fetch(orgApiPath("audit") + (qs ? `?${qs}` : ""))
      .then((r) => r.json())
      .then((d) => {
        setData(d);
        setLoading(false);
      })
      .catch(() => { setLoading(false); setError(true); });
  }, [agentFilter, actionFilter, page]);

  const entries = data?.entries || [];
  const total = data?.total || 0;

  return (
    <div className="h-full flex flex-col">
      <div className="flex items-center justify-between px-6 py-4 border-b border-neutral">
        <div className="flex items-center gap-4">
          <h1 className="text-xl font-bold text-base-content">Audit Log</h1>
          <span className="badge badge-ghost badge-sm">{total} entries</span>
        </div>
        <div className="flex gap-2">
          <input
            value={agentFilter}
            onChange={(e) => { setAgentFilter(e.target.value); setPage(0); }}
            placeholder="Filter by agent..."
            aria-label="Filter by agent"
            className="input input-xs w-32"
          />
          <input
            value={actionFilter}
            onChange={(e) => { setActionFilter(e.target.value); setPage(0); }}
            placeholder="Filter by action..."
            aria-label="Filter by action"
            className="input input-xs w-32"
          />
        </div>
      </div>

      {loading ? (
        <div className="flex-1 flex items-center justify-center">
          <span className="loading loading-spinner loading-md text-primary" />
        </div>
      ) : error ? (
        <div className="flex-1 flex flex-col items-center justify-center gap-2">
          <p className="text-error">Failed to load audit log.</p>
          <button onClick={() => setPage(page)} className="btn btn-ghost btn-xs text-error">Retry</button>
        </div>
      ) : entries.length === 0 ? (
        <div className="flex-1 flex items-center justify-center text-base-content/60">
          No audit entries yet. Tool calls will appear here.
        </div>
      ) : (
        <div className="flex-1 overflow-y-auto">
          <table className="table table-sm table-pin-rows">
            <caption className="sr-only">Audit log entries</caption>
            <thead>
              <tr>
                <th className="w-44">Timestamp</th>
                <th className="w-24">Agent</th>
                <th className="w-32">Action</th>
                <th>Details</th>
              </tr>
            </thead>
            <tbody>
              {entries.map((entry) => (
                <tr
                  key={entry.path}
                  onClick={() => setExpanded(expanded === entry.path ? null : entry.path)}
                  onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && setExpanded(expanded === entry.path ? null : entry.path)}
                  tabIndex={0}
                  role="button"
                  className="hover cursor-pointer"
                >
                  <td className="text-xs text-base-content/60 font-mono">
                    {new Date(entry.timestamp).toLocaleString()}
                  </td>
                  <td>
                    <span className="badge badge-ghost badge-xs">{entry.agent_id}</span>
                  </td>
                  <td>
                    <span className={`text-xs font-mono ${ACTION_COLORS[entry.action] || "text-base-content/60"}`}>
                      {entry.action}
                    </span>
                  </td>
                  <td>
                    {expanded === entry.path ? (
                      <pre className="text-xs text-base-content/60 whitespace-pre-wrap max-w-xl">
                        {entry.body || "(no details)"}
                      </pre>
                    ) : (
                      <span className="text-xs text-base-content/50 truncate block max-w-xl">
                        {entry.body ? entry.body.slice(0, 120).replace(/\n/g, " ") : ""}
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {total > PAGE_SIZE && (
        <div className="flex items-center justify-center gap-4 px-6 py-3 border-t border-neutral">
          <button
            disabled={page === 0}
            onClick={() => setPage(page - 1)}
            className="btn btn-ghost btn-xs"
          >
            Previous
          </button>
          <span className="text-xs text-base-content/60">
            Page {page + 1} of {Math.ceil(total / PAGE_SIZE)}
          </span>
          <button
            disabled={(page + 1) * PAGE_SIZE >= total}
            onClick={() => setPage(page + 1)}
            className="btn btn-ghost btn-xs"
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
}
