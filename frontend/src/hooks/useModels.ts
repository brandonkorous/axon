import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../utils/api";
import { queryKeys } from "../utils/queryKeys";
import { useOrgStore } from "../stores/orgStore";

// ── Types ──────────────────────────────────────────────────────────────────

export interface RegisteredModel {
  id: string;
  provider: string;
  display_name: string;
  model_type: string;
}

export interface ModelRoles {
  navigator: string;
  reasoning: string;
  memory: string;
  agent: string;
}

export interface ModelStatus {
  configured: boolean;
  model_count: number;
  roles_assigned: boolean;
}

export interface CatalogModel {
  id: string;
  name: string;
  description: string;
  tier: string;
}

export interface CatalogProvider {
  id: string;
  name: string;
  requires_key: boolean;
  models: CatalogModel[];
}

export interface ModelCatalog {
  providers: CatalogProvider[];
}

export interface ModelsResponse {
  registered_models: RegisteredModel[];
  roles: ModelRoles;
}

export interface RegisterModelPayload {
  id: string;
  display_name: string;
  model_type: "cloud" | "local";
}

// ── Queries ────────────────────────────────────────────────────────────────

export function useModels() {
  const orgId = useOrgStore((s) => s.activeOrgId);
  return useQuery({
    queryKey: queryKeys.models(orgId!),
    queryFn: () => api.get<ModelsResponse>("models"),
    enabled: !!orgId,
  });
}

export function useModelStatus() {
  const orgId = useOrgStore((s) => s.activeOrgId);
  return useQuery({
    queryKey: [...queryKeys.models(orgId!), "status"],
    queryFn: () => api.get<ModelStatus>("models/status"),
    enabled: !!orgId,
  });
}

export function useModelCatalog() {
  const orgId = useOrgStore((s) => s.activeOrgId);
  return useQuery({
    queryKey: [...queryKeys.models(orgId!), "catalog"],
    queryFn: () => api.get<ModelCatalog>("models/catalog"),
    enabled: !!orgId,
  });
}

export function useOllamaModels() {
  const orgId = useOrgStore((s) => s.activeOrgId);
  return useQuery({
    queryKey: [...queryKeys.models(orgId!), "discover"],
    queryFn: () =>
      api.get<{
        models: Array<{ id: string; name: string; size: string }>;
      }>("models/discover"),
    enabled: !!orgId,
  });
}

// ── Mutations ──────────────────────────────────────────────────────────────

export function useRegisterModel() {
  const orgId = useOrgStore((s) => s.activeOrgId);
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: RegisterModelPayload) => api.post("models", data),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: queryKeys.models(orgId!) }),
  });
}

export function useUnregisterModel() {
  const orgId = useOrgStore((s) => s.activeOrgId);
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (modelId: string) => api.del(`models/${modelId}`),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: queryKeys.models(orgId!) }),
  });
}

export function useUpdateRoles() {
  const orgId = useOrgStore((s) => s.activeOrgId);
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (roles: Partial<ModelRoles>) => api.put("models/roles", roles),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: queryKeys.models(orgId!) }),
  });
}
