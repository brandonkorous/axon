import { useQuery } from "@tanstack/react-query";
import { api } from "../utils/api";
import { queryKeys } from "../utils/queryKeys";
import { useOrgStore } from "../stores/orgStore";

// --- Types ---

export interface ConfidenceData {
  current_avg: number;
  high: number;
  medium: number;
  low: number;
  total: number;
  history: Array<{ date: string; avg: number }>;
}

export interface MemoryData {
  total_files: number;
  active: number;
  archived: number;
  total_links: number;
  by_type: Record<string, number>;
}

export interface AgentUsage {
  cost: number;
  tokens: number;
  requests: number;
}

export interface AgentMetrics {
  id: string;
  name: string;
  title: string;
  color: string;
  status: string;
  model: string;
  confidence: ConfidenceData;
  memory: MemoryData;
  usage: AgentUsage;
  message_count: number;
}

export interface TaskMetrics {
  total: number;
  completed: number;
  in_progress: number;
  pending: number;
  completion_rate: number;
  by_agent: Record<string, { completed: number; total: number }>;
}

export interface ActivityDay {
  date: string;
  actions: number;
  unique_agents: number;
}

export interface DelegationEdge {
  from: string;
  to: string;
  count: number;
}

export interface AnalyticsData {
  agents: AgentMetrics[];
  totals: {
    total_agents: number;
    total_cost: number;
    total_tokens: number;
    total_requests: number;
    total_vault_files: number;
    total_links: number;
    avg_confidence: number;
  };
  tasks: TaskMetrics;
  activity_timeline: ActivityDay[];
  tool_usage: Record<string, number>;
  delegation_flow: DelegationEdge[];
}

// --- Queries ---

export function useAnalytics() {
  const orgId = useOrgStore((s) => s.activeOrgId);
  return useQuery({
    queryKey: queryKeys.analytics(orgId),
    queryFn: () => api.get<AnalyticsData>("analytics"),
    enabled: !!orgId,
  });
}
