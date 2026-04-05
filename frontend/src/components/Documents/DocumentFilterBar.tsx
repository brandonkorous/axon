import type { AgentDocCount } from "../../hooks/useDocuments";

interface Props {
  search: string;
  onSearchChange: (value: string) => void;
  typeFilter: string;
  onTypeChange: (value: string) => void;
  agentFilter: string;
  onAgentChange: (value: string) => void;
  types: string[];
  agents: AgentDocCount[];
  hasFilters: boolean;
  onClear: () => void;
}

export function DocumentFilterBar({
  search,
  onSearchChange,
  typeFilter,
  onTypeChange,
  agentFilter,
  onAgentChange,
  types,
  agents,
  hasFilters,
  onClear,
}: Props) {
  return (
    <div className="flex items-center gap-3 px-6 py-3 border-b border-neutral bg-base-200/50">
      <input
        type="text"
        value={search}
        onChange={(e) => onSearchChange(e.target.value)}
        placeholder="Search documents..."
        aria-label="Search documents"
        className="input input-sm w-64"
      />

      <select
        value={agentFilter}
        onChange={(e) => onAgentChange(e.target.value)}
        aria-label="Filter by agent"
        className="select select-sm"
      >
        <option value="">All agents</option>
        {agents.map((a) => (
          <option key={a.id} value={a.id}>
            {a.name} ({a.doc_count})
          </option>
        ))}
      </select>

      <select
        value={typeFilter}
        onChange={(e) => onTypeChange(e.target.value)}
        aria-label="Filter by type"
        className="select select-sm"
      >
        <option value="">All types</option>
        {types.map((t) => (
          <option key={t} value={t}>{t}</option>
        ))}
      </select>

      {hasFilters && (
        <button
          onClick={onClear}
          className="btn btn-ghost btn-xs text-base-content/50"
        >
          Clear
        </button>
      )}
    </div>
  );
}
