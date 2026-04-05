import { useQuery } from "@tanstack/react-query";
import { api } from "../utils/api";
import { queryKeys } from "../utils/queryKeys";
import { useOrgStore } from "../stores/orgStore";

export interface OrgDocument {
  path: string;
  name: string;
  description: string;
  type: string;
  tags: string;
  content_preview: string;
  confidence: number;
  status: string;
  date: string;
  link_count: number;
  backlink_count: number;
  last_modified: string;
  agent_id: string;
  agent_name: string;
}

export interface AgentDocCount {
  id: string;
  name: string;
  doc_count: number;
}

export interface DocumentsResponse {
  documents: OrgDocument[];
  total: number;
  agents: AgentDocCount[];
  types: string[];
}

export interface DocumentFilters {
  q?: string;
  type?: string;
  agent_id?: string;
  branch?: string;
  tags?: string;
  limit?: number;
  offset?: number;
}

function buildDocPath(filters: DocumentFilters): string {
  const params = new URLSearchParams();
  if (filters.q) params.set("q", filters.q);
  if (filters.type) params.set("type", filters.type);
  if (filters.agent_id) params.set("agent_id", filters.agent_id);
  if (filters.branch) params.set("branch", filters.branch);
  if (filters.tags) params.set("tags", filters.tags);
  if (filters.limit) params.set("limit", String(filters.limit));
  if (filters.offset) params.set("offset", String(filters.offset));
  const qs = params.toString();
  return qs ? `vaults/documents?${qs}` : "vaults/documents";
}

export function useDocuments(filters: DocumentFilters = {}) {
  const orgId = useOrgStore((s) => s.activeOrgId);
  return useQuery({
    queryKey: queryKeys.documents(orgId, filters as Record<string, unknown>),
    queryFn: () => api.get<DocumentsResponse>(buildDocPath(filters)),
    enabled: !!orgId,
  });
}
