import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../utils/api";
import { queryKeys } from "../utils/queryKeys";
import { useOrgStore } from "../stores/orgStore";

// --- Types ---

export interface IssueComment {
  author: string;
  type: string;
  created_at: string;
  body: string;
}

export interface Issue {
  path: string;
  name: string;
  type: string;
  id: number;
  assignee: string;
  status: "open" | "in_progress" | "resolved" | "closed";
  priority: "p0" | "p1" | "p2" | "p3";
  labels: string[];
  parent_issue: string;
  created_by: string;
  created_at: string;
  updated_at: string;
  body: string;
  comment_count?: number;
  comments?: IssueComment[];
}

export interface IssueFilters {
  status?: string;
  assignee?: string;
  priority?: string;
  label?: string;
}

export interface CreateIssueInput {
  title: string;
  description?: string;
  assignee?: string;
  priority?: string;
  labels?: string[];
}

// --- Helpers ---

function buildIssuePath(filters?: IssueFilters): string {
  const parts: string[] = [];
  if (filters?.status) parts.push(`status=${filters.status}`);
  if (filters?.assignee) parts.push(`assignee=${filters.assignee}`);
  if (filters?.priority) parts.push(`priority=${filters.priority}`);
  if (filters?.label) parts.push(`label=${filters.label}`);
  return parts.length ? `issues?${parts.join("&")}` : "issues";
}

// --- Queries ---

export function useIssues(filters?: IssueFilters) {
  const orgId = useOrgStore((s) => s.activeOrgId);
  return useQuery({
    queryKey: queryKeys.issues(orgId, filters as Record<string, unknown> | undefined),
    queryFn: () => api.get<Issue[]>(buildIssuePath(filters)),
    enabled: !!orgId,
  });
}

// --- Mutations ---

export function useCreateIssue() {
  const queryClient = useQueryClient();
  const orgId = useOrgStore((s) => s.activeOrgId);
  return useMutation({
    mutationFn: (data: CreateIssueInput) => api.post<Issue>("issues", data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.issues(orgId) });
    },
  });
}

export function useUpdateIssue() {
  const queryClient = useQueryClient();
  const orgId = useOrgStore((s) => s.activeOrgId);
  return useMutation({
    mutationFn: ({ path, data }: { path: string; data: Record<string, unknown> }) => {
      const issuePath = path.startsWith("issues/") ? path.slice(7) : path;
      return api.put(`issues/${issuePath}`, data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.issues(orgId) });
    },
  });
}

export function useAddComment() {
  const queryClient = useQueryClient();
  const orgId = useOrgStore((s) => s.activeOrgId);
  return useMutation({
    mutationFn: ({
      issueId,
      content,
    }: {
      issueId: number | string;
      content: string;
    }) => api.post(`issues/${issueId}/comments`, { content }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.issues(orgId) });
    },
  });
}
