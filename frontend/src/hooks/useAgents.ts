import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../utils/api";
import { queryKeys } from "../utils/queryKeys";
import { useOrgStore } from "../stores/orgStore";

// --- Types ---

export interface LifecycleState {
  agent_id: string;
  status: "active" | "paused" | "disabled" | "terminated";
  strategy_override: string | null;
  rate_limit: { max_per_minute: number };
  paused_at: number | null;
  terminated_at: number | null;
  queued_messages: number;
}

export interface AgentInfo {
  id: string;
  name: string;
  title: string;
  title_tag: string;
  tagline: string;
  ui: {
    color: string;
    avatar: string;
    sparkle_color: string;
  };
  type: "advisor" | "orchestrator" | "huddle" | "external";
  parent_id?: string;
  model: string;
  status: string;
  lifecycle?: LifecycleState;
  system_prompt?: string;
  email?: string | null;
  comms_enabled?: boolean;
  email_alias?: string;
  action_bias?: "proactive" | "balanced" | "deliberative";
  plugins?: {
    shell_access?: {
      enabled: boolean;
      path: string;
      executables: string[];
    };
    sandbox?: {
      enabled: boolean;
      path: string;
      executables: string[];
      image: string;
    };
  };
  plugin_names?: string[];
  runner_status?: "running" | "stopped" | "unknown";
}

export interface PersonaUpdate {
  name?: string;
  title?: string;
  title_tag?: string;
  tagline?: string;
  system_prompt?: string;
  color?: string;
  sparkle_color?: string;
  comms_enabled?: boolean;
  email_alias?: string;
  action_bias?: "proactive" | "balanced" | "deliberative";
}

// --- Queries ---

export function useAgents() {
  const orgId = useOrgStore((s) => s.activeOrgId);
  return useQuery({
    queryKey: queryKeys.agents(orgId),
    queryFn: () =>
      api.get<{ agents: AgentInfo[] }>("agents").then((d) => d.agents),
    enabled: !!orgId,
  });
}

export function useAgent(agentId: string | undefined) {
  const orgId = useOrgStore((s) => s.activeOrgId);
  return useQuery({
    queryKey: queryKeys.agent(orgId, agentId ?? ""),
    queryFn: () => api.get<AgentInfo>(`agents/${agentId}`),
    enabled: !!orgId && !!agentId,
  });
}

// --- Mutations ---

export function useUpdatePersona() {
  const queryClient = useQueryClient();
  const orgId = useOrgStore((s) => s.activeOrgId);
  return useMutation({
    mutationFn: ({
      agentId,
      update,
    }: {
      agentId: string;
      update: PersonaUpdate;
    }) => api.patch<AgentInfo>(`agents/${agentId}`, update),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.agents(orgId) });
    },
  });
}

export function useDeleteAgent() {
  const queryClient = useQueryClient();
  const orgId = useOrgStore((s) => s.activeOrgId);
  return useMutation({
    mutationFn: (agentId: string) => api.del(`lifecycle/${agentId}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.agents(orgId) });
    },
  });
}

export function useLifecycleAction() {
  const queryClient = useQueryClient();
  const orgId = useOrgStore((s) => s.activeOrgId);
  return useMutation({
    mutationFn: ({
      agentId,
      action,
      body,
    }: {
      agentId: string;
      action: string;
      body?: object;
    }) => api.post(`lifecycle/${agentId}/${action}`, body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.agents(orgId) });
    },
  });
}

export function useStartRunner() {
  const queryClient = useQueryClient();
  const orgId = useOrgStore((s) => s.activeOrgId);
  return useMutation({
    mutationFn: (agentId: string) =>
      api.post(`agents/${agentId}/runner/start`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.agents(orgId) });
    },
  });
}

export function useStopRunner() {
  const queryClient = useQueryClient();
  const orgId = useOrgStore((s) => s.activeOrgId);
  return useMutation({
    mutationFn: (agentId: string) =>
      api.post(`agents/${agentId}/runner/stop`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.agents(orgId) });
    },
  });
}
