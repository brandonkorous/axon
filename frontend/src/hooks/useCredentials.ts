import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../utils/api";
import { queryKeys } from "../utils/queryKeys";
import { useOrgStore } from "../stores/orgStore";

// ── Types ──────────────────────────────────────────────────────────────────

export interface Credential {
  id: string;
  provider: string;
  label: string;
  token_preview: string;
  created_at: string;
}

export interface CredentialCreatePayload {
  provider: string;
  access_token: string;
  label?: string;
}

// ── Queries ────────────────────────────────────────────────────────────────

export function useCredentials() {
  const orgId = useOrgStore((s) => s.activeOrgId);
  return useQuery({
    queryKey: queryKeys.credentials(orgId!),
    queryFn: () => api.get<Credential[]>("credentials"),
    enabled: !!orgId,
  });
}

// ── Mutations ──────────────────────────────────────────────────────────────

export function useCreateCredential() {
  const orgId = useOrgStore((s) => s.activeOrgId);
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: CredentialCreatePayload) =>
      api.post("credentials", data),
    onSuccess: () =>
      queryClient.invalidateQueries({
        queryKey: queryKeys.credentials(orgId!),
      }),
  });
}

export function useDeleteCredential() {
  const orgId = useOrgStore((s) => s.activeOrgId);
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (credentialId: string) =>
      api.del(`credentials/${credentialId}`),
    onSuccess: () =>
      queryClient.invalidateQueries({
        queryKey: queryKeys.credentials(orgId!),
      }),
  });
}
