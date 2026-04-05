import { useQuery } from "@tanstack/react-query";
import { api } from "../utils/api";
import { queryKeys } from "../utils/queryKeys";
import { useOrgStore } from "../stores/orgStore";

// --- Types ---

export interface UsageRecord {
  ts: string;
  model: string;
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
  cost: number;
  agent_id: string;
  call_type: string;
  caller: string;
}

export interface BreakdownEntry {
  cost: number;
  tokens: number;
  count: number;
}

export interface UsageSummary {
  total_cost: number;
  total_tokens: number;
  total_requests: number;
  by_model: Record<string, BreakdownEntry>;
  by_agent: Record<string, BreakdownEntry>;
}

// --- Queries ---

export function useUsageSummary(dateFrom: string, dateTo: string) {
  const orgId = useOrgStore((s) => s.activeOrgId);
  return useQuery({
    queryKey: [...queryKeys.usage(orgId), "summary", dateFrom, dateTo],
    queryFn: () =>
      api.get<UsageSummary>(
        `usage/summary?date_from=${dateFrom}&date_to=${dateTo}`,
      ),
    enabled: !!orgId && !!dateFrom && !!dateTo,
  });
}

export function useUsageRecords(
  dateFrom: string,
  dateTo: string,
  limit = 100,
  offset = 0,
) {
  const orgId = useOrgStore((s) => s.activeOrgId);
  return useQuery({
    queryKey: [
      ...queryKeys.usage(orgId),
      "records",
      dateFrom,
      dateTo,
      limit,
      offset,
    ],
    queryFn: () =>
      api.get<{ records: UsageRecord[]; total: number }>(
        `usage?date_from=${dateFrom}&date_to=${dateTo}&limit=${limit}&offset=${offset}`,
      ),
    enabled: !!orgId && !!dateFrom && !!dateTo,
  });
}
