import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../utils/api";
import { queryKeys } from "../utils/queryKeys";
import { useOrgStore } from "../stores/orgStore";

// --- Types ---

export interface HostAgent {
  id: string;
  name: string;
  path: string;
  port: number;
  host: string;
  executables: string[];
  status: string;
}

// --- Queries ---

export function useHostAgents() {
  const orgId = useOrgStore((s) => s.activeOrgId);
  return useQuery({
    queryKey: queryKeys.hostAgents(orgId),
    queryFn: async () => {
      const data = await api.get<{
        host_agents?: HostAgent[];
        agents?: HostAgent[];
      }>("host-agents");
      return data.host_agents || data.agents || [];
    },
    enabled: !!orgId,
  });
}

export function useManagerStatus() {
  const orgId = useOrgStore((s) => s.activeOrgId);
  return useQuery({
    queryKey: [...queryKeys.hostAgents(orgId), "manager-status"],
    queryFn: () =>
      api.get<{ manager_running: boolean; host_orgs_path?: string }>(
        "host-agents/manager-status",
      ),
    enabled: !!orgId,
  });
}

// --- Mutations ---

export function useRegisterHostAgent() {
  const queryClient = useQueryClient();
  const orgId = useOrgStore((s) => s.activeOrgId);
  return useMutation({
    mutationFn: (
      agent: Pick<HostAgent, "id" | "name" | "path" | "port" | "executables">,
    ) => api.post<HostAgent>("host-agents", agent),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.hostAgents(orgId) });
    },
  });
}

export function useUpdateHostAgent() {
  const queryClient = useQueryClient();
  const orgId = useOrgStore((s) => s.activeOrgId);
  return useMutation({
    mutationFn: ({ id, ...partial }: { id: string } & Partial<HostAgent>) =>
      api.patch<HostAgent>(`host-agents/${id}`, partial),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.hostAgents(orgId) });
    },
  });
}

export function useDeleteHostAgent() {
  const queryClient = useQueryClient();
  const orgId = useOrgStore((s) => s.activeOrgId);
  return useMutation({
    mutationFn: (id: string) => api.del(`host-agents/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.hostAgents(orgId) });
    },
  });
}

export function useStartHostAgent() {
  const queryClient = useQueryClient();
  const orgId = useOrgStore((s) => s.activeOrgId);
  return useMutation({
    mutationFn: (id: string) => api.post(`host-agents/${id}/start`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.hostAgents(orgId) });
    },
  });
}

export function useStopHostAgent() {
  const queryClient = useQueryClient();
  const orgId = useOrgStore((s) => s.activeOrgId);
  return useMutation({
    mutationFn: (id: string) => api.post(`host-agents/${id}/stop`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.hostAgents(orgId) });
    },
  });
}

export function useRestartHostAgent() {
  const queryClient = useQueryClient();
  const orgId = useOrgStore((s) => s.activeOrgId);
  return useMutation({
    mutationFn: (id: string) => api.post(`host-agents/${id}/restart`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.hostAgents(orgId) });
    },
  });
}
