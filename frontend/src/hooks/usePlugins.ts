import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../utils/api";
import { queryKeys } from "../utils/queryKeys";
import { useOrgStore } from "../stores/orgStore";

// ── Types ──────────────────────────────────────────────────────────────────

export interface PluginInfo {
  name: string;
  description: string;
  version: string;
  author: string;
  category: string;
  icon: string;
  auto_load: boolean;
  triggers: string[];
  tools: string[];
  required_credentials: string[];
  is_builtin: boolean;
  source: string;
  sandbox_type: string;
}

export interface ToolInfo {
  name: string;
  description: string;
  parameters: Record<string, unknown>;
}

export interface PluginInstanceInfo {
  id: string;
  plugin: string;
  name: string;
  agents: string[];
  config: Record<string, unknown>;
}

export interface PluginDetail extends Omit<PluginInfo, "tools"> {
  tools: ToolInfo[];
  python_deps: string[];
  agents_using: string[];
  instances: PluginInstanceInfo[];
  sandbox_type: string;
}

export interface PluginCreatePayload {
  name: string;
  version?: string;
  description?: string;
  category?: string;
  icon?: string;
  triggers?: string[];
  tools?: string[];
  required_credentials?: string[];
  [key: string]: unknown;
}

// ── Queries ────────────────────────────────────────────────────────────────

export function usePlugins() {
  const orgId = useOrgStore((s) => s.activeOrgId);
  return useQuery({
    queryKey: queryKeys.plugins(orgId!),
    queryFn: () =>
      api.get<{ plugins: PluginInfo[] }>("plugins").then((d) => d.plugins),
    enabled: !!orgId,
  });
}

export function usePluginDetail(name: string | undefined) {
  const orgId = useOrgStore((s) => s.activeOrgId);
  return useQuery({
    queryKey: [...queryKeys.plugins(orgId!), name],
    queryFn: () => api.get<PluginDetail>(`plugins/${name}`),
    enabled: !!orgId && !!name,
  });
}

// ── Mutations ──────────────────────────────────────────────────────────────

export function useEnablePlugin() {
  const orgId = useOrgStore((s) => s.activeOrgId);
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (vars: { pluginName: string; agent_id: string }) =>
      api.post(`plugins/${vars.pluginName}/enable`, {
        agent_id: vars.agent_id,
      }),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: queryKeys.plugins(orgId!) }),
  });
}

export function useDisablePlugin() {
  const orgId = useOrgStore((s) => s.activeOrgId);
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (vars: { pluginName: string; agent_id: string }) =>
      api.post(`plugins/${vars.pluginName}/disable`, {
        agent_id: vars.agent_id,
      }),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: queryKeys.plugins(orgId!) }),
  });
}

export function useSetPluginConfig() {
  const orgId = useOrgStore((s) => s.activeOrgId);
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (vars: {
      pluginName: string;
      agent_id: string;
      config: Record<string, unknown>;
    }) =>
      api.put(`plugins/${vars.pluginName}/config`, {
        agent_id: vars.agent_id,
        config: vars.config,
      }),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: queryKeys.plugins(orgId!) }),
  });
}

export function useCreatePlugin() {
  const orgId = useOrgStore((s) => s.activeOrgId);
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: PluginCreatePayload) => api.post("plugins", data),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: queryKeys.plugins(orgId!) }),
  });
}

export function useDeletePlugin() {
  const orgId = useOrgStore((s) => s.activeOrgId);
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (name: string) => api.del(`plugins/${name}`),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: queryKeys.plugins(orgId!) }),
  });
}

export function useCreateInstance() {
  const orgId = useOrgStore((s) => s.activeOrgId);
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (vars: {
      pluginName: string;
      id: string;
      name?: string;
      agents?: string[];
      config?: Record<string, unknown>;
    }) => {
      const { pluginName, ...body } = vars;
      return api.post(`plugins/${pluginName}/instances`, body);
    },
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: queryKeys.plugins(orgId!) }),
  });
}

export function useUpdateInstance() {
  const orgId = useOrgStore((s) => s.activeOrgId);
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (vars: {
      pluginName: string;
      instanceId: string;
      name?: string;
      agents?: string[];
      config?: Record<string, unknown>;
    }) => {
      const { pluginName, instanceId, ...body } = vars;
      return api.put(`plugins/${pluginName}/instances/${instanceId}`, body);
    },
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: queryKeys.plugins(orgId!) }),
  });
}

export function useDeleteInstance() {
  const orgId = useOrgStore((s) => s.activeOrgId);
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (vars: { pluginName: string; instanceId: string }) =>
      api.del(`plugins/${vars.pluginName}/instances/${vars.instanceId}`),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: queryKeys.plugins(orgId!) }),
  });
}
