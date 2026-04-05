import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../utils/api";
import { queryKeys } from "../utils/queryKeys";
import { useOrgStore } from "../stores/orgStore";

// --- Types ---

export interface SandboxImageInfo {
  type: string;
  description: string;
  estimated_size_mb: number;
  tools: string[];
  status: "idle" | "building" | "ready" | "error";
  size_mb?: number;
  agents_using: string[];
  plugins_requiring: string[];
}

export interface RunningInstance {
  instance_id: string;
  instance_name: string;
  plugin: string;
  agents: string[];
  sandbox_id?: string;
  status: string;
}

// --- Queries ---

export function useSandboxImages() {
  const orgId = useOrgStore((s) => s.activeOrgId);
  return useQuery({
    queryKey: queryKeys.sandboxImages(orgId),
    queryFn: () =>
      api
        .get<{ images: SandboxImageInfo[] }>("sandbox/images")
        .then((d) => d.images),
    enabled: !!orgId,
  });
}

export function useRunningInstances() {
  const orgId = useOrgStore((s) => s.activeOrgId);
  return useQuery({
    queryKey: queryKeys.sandboxContainers(orgId),
    queryFn: () =>
      api
        .get<{ instances: RunningInstance[] }>("sandbox/running")
        .then((d) => d.instances),
    enabled: !!orgId,
  });
}

// --- Mutations ---

export function useBuildImage() {
  const queryClient = useQueryClient();
  const orgId = useOrgStore((s) => s.activeOrgId);
  return useMutation({
    mutationFn: (type: string) =>
      api.post(`sandbox/images/${type}/build`),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.sandboxImages(orgId),
      });
    },
  });
}

export function useRemoveImage() {
  const queryClient = useQueryClient();
  const orgId = useOrgStore((s) => s.activeOrgId);
  return useMutation({
    mutationFn: (type: string) => api.del(`sandbox/images/${type}`),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.sandboxImages(orgId),
      });
    },
  });
}

export function useStopInstance() {
  const queryClient = useQueryClient();
  const orgId = useOrgStore((s) => s.activeOrgId);
  return useMutation({
    mutationFn: (instanceId: string) =>
      api.post(`sandbox/running/${instanceId}/stop`),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.sandboxContainers(orgId),
      });
    },
  });
}
