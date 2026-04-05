import { useState, useMemo, useCallback } from "react";
import { useDocuments, type DocumentFilters, type OrgDocument } from "../../hooks/useDocuments";
import { useAgents } from "../../hooks/useAgents";
import { DocumentDrawer } from "./DocumentDrawer";
import { DocumentFilterBar } from "./DocumentFilterBar";

const DEBOUNCE_MS = 300;
const PAGE_SIZE = 50;

export function DocumentLibrary() {
  const [search, setSearch] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [typeFilter, setTypeFilter] = useState("");
  const [agentFilter, setAgentFilter] = useState("");
  const [offset, setOffset] = useState(0);
  const [selected, setSelected] = useState<OrgDocument | null>(null);

  // Debounce search input
  const debounceRef = useState<ReturnType<typeof setTimeout> | null>(null);
  const handleSearch = useCallback((value: string) => {
    setSearch(value);
    if (debounceRef[0]) clearTimeout(debounceRef[0]);
    debounceRef[0] = setTimeout(() => {
      setDebouncedSearch(value);
      setOffset(0);
    }, DEBOUNCE_MS);
  }, [debounceRef]);

  const filters: DocumentFilters = useMemo(() => ({
    q: debouncedSearch || undefined,
    type: typeFilter || undefined,
    agent_id: agentFilter || undefined,
    limit: PAGE_SIZE,
    offset,
  }), [debouncedSearch, typeFilter, agentFilter, offset]);

  const { data, isLoading, isError, refetch } = useDocuments(filters);
  const { data: agents = [] } = useAgents();

  const agentColorMap = useMemo(() => {
    const map: Record<string, string> = {};
    for (const a of agents) map[a.id] = a.ui?.color || "var(--color-primary)";
    return map;
  }, [agents]);

  const documents = data?.documents ?? [];
  const total = data?.total ?? 0;
  const agentCounts = data?.agents ?? [];
  const types = data?.types ?? [];

  const hasMore = offset + PAGE_SIZE < total;
  const hasPrev = offset > 0;

  const clearFilters = () => {
    setSearch("");
    setDebouncedSearch("");
    setTypeFilter("");
    setAgentFilter("");
    setOffset(0);
  };

  const hasFilters = !!debouncedSearch || !!typeFilter || !!agentFilter;

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-neutral">
        <div className="flex items-center gap-3">
          <h1 className="text-xl font-bold text-base-content">Documents</h1>
          {!isLoading && (
            <span className="text-sm text-base-content/50">{total} total</span>
          )}
        </div>
      </div>

      {/* Filters */}
      <DocumentFilterBar
        search={search}
        onSearchChange={handleSearch}
        typeFilter={typeFilter}
        onTypeChange={(v) => { setTypeFilter(v); setOffset(0); }}
        agentFilter={agentFilter}
        onAgentChange={(v) => { setAgentFilter(v); setOffset(0); }}
        types={types}
        agents={agentCounts}
        hasFilters={hasFilters}
        onClear={clearFilters}
      />

      {/* Content */}
      {isLoading ? (
        <div className="flex-1 flex items-center justify-center">
          <span className="loading loading-spinner loading-md text-primary" />
        </div>
      ) : isError ? (
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <p className="text-sm text-error mb-2">Failed to load documents.</p>
            <button onClick={() => refetch()} className="link link-accent text-xs">Try again</button>
          </div>
        </div>
      ) : documents.length === 0 ? (
        <div className="flex-1 flex items-center justify-center text-base-content/60">
          {hasFilters ? "No documents match these filters" : "No documents yet. Agents will generate them as they work."}
        </div>
      ) : (
        <>
          <div className="flex-1 overflow-y-auto">
            <table className="table table-sm table-pin-rows">
              <caption className="sr-only">Document library</caption>
              <thead>
                <tr>
                  <th>Name</th>
                  <th className="w-28">Agent</th>
                  <th className="w-24">Type</th>
                  <th className="w-28">Date</th>
                  <th className="w-16 text-right">Links</th>
                </tr>
              </thead>
              <tbody>
                {documents.map((doc) => (
                  <DocumentRow
                    key={`${doc.agent_id}:${doc.path}`}
                    doc={doc}
                    agentColor={agentColorMap[doc.agent_id]}
                    onSelect={setSelected}
                  />
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {(hasPrev || hasMore) && (
            <div className="flex items-center justify-between px-6 py-2 border-t border-neutral text-sm">
              <span className="text-base-content/50">
                {offset + 1}–{Math.min(offset + PAGE_SIZE, total)} of {total}
              </span>
              <div className="join">
                <button
                  className="join-item btn btn-ghost btn-xs"
                  disabled={!hasPrev}
                  onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))}
                >
                  Prev
                </button>
                <button
                  className="join-item btn btn-ghost btn-xs"
                  disabled={!hasMore}
                  onClick={() => setOffset(offset + PAGE_SIZE)}
                >
                  Next
                </button>
              </div>
            </div>
          )}
        </>
      )}

      {/* Document drawer */}
      {selected && (
        <DocumentDrawer
          vaultId={selected.agent_id}
          filePath={selected.path}
          onClose={() => setSelected(null)}
          onNavigate={(path) => {
            setSelected({ ...selected, path });
          }}
        />
      )}
    </div>
  );
}

function DocumentRow({
  doc,
  agentColor,
  onSelect,
}: {
  doc: OrgDocument;
  agentColor?: string;
  onSelect: (doc: OrgDocument) => void;
}) {
  const displayName = doc.name || doc.path.split("/").pop()?.replace(/\.md$/, "") || doc.path;
  const preview = doc.content_preview?.slice(0, 120);

  return (
    <tr
      onClick={() => onSelect(doc)}
      onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && onSelect(doc)}
      tabIndex={0}
      role="button"
      className="hover cursor-pointer"
    >
      <td>
        <div>
          <span className="text-sm font-medium text-base-content">{displayName}</span>
          {preview && (
            <p className="text-xs text-base-content/50 truncate max-w-md mt-0.5">{preview}</p>
          )}
        </div>
      </td>
      <td>
        <span className="flex items-center gap-1.5 text-sm">
          <span
            className="w-2 h-2 rounded-full shrink-0"
            style={{ backgroundColor: agentColor || "var(--color-primary)" }}
          />
          <span className="truncate text-base-content/70">{doc.agent_name}</span>
        </span>
      </td>
      <td>
        {doc.type && (
          <span className="badge badge-soft badge-ghost badge-xs">{doc.type}</span>
        )}
      </td>
      <td className="text-sm text-base-content/60">
        {doc.date || (doc.last_modified ? new Date(doc.last_modified).toLocaleDateString() : "")}
      </td>
      <td className="text-sm text-base-content/50 text-right">
        {(doc.link_count || 0) + (doc.backlink_count || 0) > 0
          ? `${doc.link_count || 0}/${doc.backlink_count || 0}`
          : ""}
      </td>
    </tr>
  );
}
