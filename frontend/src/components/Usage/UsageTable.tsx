import type { UsageRecord } from "../../stores/usageStore";
import { formatCost } from "../../utils/format";

interface Props {
  records: UsageRecord[];
  total: number;
  page: number;
  pageSize: number;
  onPageChange: (page: number) => void;
}

function formatTime(ts: string): string {
  if (!ts) return "";
  return new Date(ts).toLocaleString();
}

function shortModel(model: string): string {
  const parts = model.split("/");
  return parts.length > 1 ? parts[parts.length - 1] : model;
}

export function UsageTable({
  records,
  total,
  page,
  pageSize,
  onPageChange,
}: Props) {
  const totalPages = Math.ceil(total / pageSize);

  if (records.length === 0) {
    return (
      <div className="card card-border bg-base-300/30">
        <div className="card-body p-5">
          <h2 className="text-base font-semibold text-base-content mb-4">
            Request Log
          </h2>
          <p className="text-sm text-base-content/60">
            No usage records yet. Interact with agents to start tracking.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="card card-border bg-base-300/30">
      <div className="card-body p-5">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-base font-semibold text-base-content">
            Request Log
          </h2>
          <span className="badge badge-ghost badge-sm">
            {total.toLocaleString()} requests
          </span>
        </div>
        <div className="overflow-x-auto">
          <table className="table table-sm table-pin-rows">
            <caption className="sr-only">LLM usage records</caption>
            <thead>
              <tr>
                <th className="w-40">Time</th>
                <th className="w-20">Agent</th>
                <th className="w-36">Model</th>
                <th className="w-20 text-right">Prompt</th>
                <th className="w-20 text-right">Completion</th>
                <th className="w-20 text-right">Cost</th>
                <th className="w-24">Caller</th>
              </tr>
            </thead>
            <tbody>
              {records.map((r, i) => (
                <tr key={`${r.ts}-${i}`} className="hover">
                  <td className="text-xs text-base-content/60 font-mono">
                    {formatTime(r.ts)}
                  </td>
                  <td>
                    <span className="badge badge-ghost badge-xs">
                      {r.agent_id || "-"}
                    </span>
                  </td>
                  <td
                    className="text-xs text-base-content/60 font-mono truncate max-w-[9rem]"
                    title={r.model}
                  >
                    {shortModel(r.model)}
                  </td>
                  <td className="text-xs text-right text-base-content/60 font-mono">
                    {r.prompt_tokens.toLocaleString()}
                  </td>
                  <td className="text-xs text-right text-base-content/60 font-mono">
                    {r.completion_tokens.toLocaleString()}
                  </td>
                  <td className="text-xs text-right text-base-content font-mono font-medium">
                    {formatCost(r.cost)}
                  </td>
                  <td className="text-xs text-base-content/60">
                    {r.caller}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {totalPages > 1 && (
          <div className="flex items-center justify-center gap-4 pt-3 border-t border-neutral mt-3">
            <button
              disabled={page === 0}
              onClick={() => onPageChange(page - 1)}
              className="btn btn-ghost btn-xs"
            >
              Previous
            </button>
            <span className="text-xs text-base-content/60">
              Page {page + 1} of {totalPages}
            </span>
            <button
              disabled={page + 1 >= totalPages}
              onClick={() => onPageChange(page + 1)}
              className="btn btn-ghost btn-xs"
            >
              Next
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
