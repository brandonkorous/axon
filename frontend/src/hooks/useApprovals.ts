import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../utils/api";
import { queryKeys } from "../utils/queryKeys";
import { useOrgStore } from "../stores/orgStore";

// --- Types ---

export interface CommsPayload {
  to?: string;
  subject?: string;
  body?: string;
  cc?: string;
  target?: string;
  content?: string;
  is_dm?: boolean;
}

export interface Approval {
  task_path: string;
  title: string;
  plan_content: string;
  files_affected: string[];
  delegated_by: string;
  type: string;
  channel?: string;
  comms_payload?: CommsPayload;
}

export interface ApprovalHistoryItem {
  task_path: string;
  title: string;
  status: string;
  created_by: string;
  created_at: string;
  approved_at?: string;
  decline_reason?: string;
  channel?: string;
  type?: string;
}

export interface ApprovalHistoryFilters {
  status?: string;
  channel?: string;
}

// --- Queries ---

export function usePendingApprovals() {
  const orgId = useOrgStore((s) => s.activeOrgId);
  return useQuery({
    queryKey: [...queryKeys.approvals(orgId), "pending"],
    queryFn: () => api.get<Approval[]>("approvals/pending"),
    enabled: !!orgId,
  });
}

export function useApprovalHistory(filters?: ApprovalHistoryFilters) {
  const orgId = useOrgStore((s) => s.activeOrgId);
  return useQuery({
    queryKey: [...queryKeys.approvals(orgId), "history", filters],
    queryFn: () => {
      const params = new URLSearchParams();
      if (filters?.status) params.set("status", filters.status);
      if (filters?.channel) params.set("channel", filters.channel);
      const qs = params.toString();
      return api.get<ApprovalHistoryItem[]>(
        qs ? `approvals/history?${qs}` : "approvals/history",
      );
    },
    enabled: !!orgId,
  });
}

// --- Mutations ---

export function useApprove() {
  const queryClient = useQueryClient();
  const orgId = useOrgStore((s) => s.activeOrgId);
  return useMutation({
    mutationFn: (taskPath: string) =>
      api.post(`approvals/${taskPath}/approve`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.approvals(orgId) });
    },
  });
}

export function useDecline() {
  const queryClient = useQueryClient();
  const orgId = useOrgStore((s) => s.activeOrgId);
  return useMutation({
    mutationFn: ({
      taskPath,
      reason,
    }: {
      taskPath: string;
      reason?: string;
    }) => api.post(`approvals/${taskPath}/decline`, reason ? { reason } : undefined),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.approvals(orgId) });
    },
  });
}
