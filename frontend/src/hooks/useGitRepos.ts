import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../utils/api";
import { queryKeys } from "../utils/queryKeys";
import { useOrgStore } from "../stores/orgStore";

// ── Types ──────────────────────────────────────────────────────────────────

export interface GitRepo {
  id: string;
  org_id: string;
  url: string;
  name: string;
  default_branch: string;
  auth_credential_id: string | null;
  clone_strategy: "shallow" | "full" | "sparse";
  sparse_paths: string[];
}

export interface GitRepoCreateData {
  url: string;
  name?: string;
  default_branch?: string;
  auth_credential_id?: string | null;
  clone_strategy?: "shallow" | "full" | "sparse";
  sparse_paths?: string[];
}

export interface GitRepoUpdateData {
  url?: string;
  name?: string;
  default_branch?: string;
  auth_credential_id?: string | null;
  clone_strategy?: "shallow" | "full" | "sparse";
  sparse_paths?: string[];
}

// ── Queries ────────────────────────────────────────────────────────────────

export function useGitRepos() {
  const orgId = useOrgStore((s) => s.activeOrgId);
  return useQuery({
    queryKey: queryKeys.gitRepos(orgId!),
    queryFn: () =>
      api.get<{ repos: GitRepo[] }>("git-repos").then((d) => d.repos),
    enabled: !!orgId,
  });
}

// ── Mutations ──────────────────────────────────────────────────────────────

export function useCreateRepo() {
  const orgId = useOrgStore((s) => s.activeOrgId);
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: GitRepoCreateData) => api.post("git-repos", data),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: queryKeys.gitRepos(orgId!) }),
  });
}

export function useUpdateRepo() {
  const orgId = useOrgStore((s) => s.activeOrgId);
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (vars: { repoId: string } & GitRepoUpdateData) => {
      const { repoId, ...body } = vars;
      return api.patch(`git-repos/${repoId}`, body);
    },
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: queryKeys.gitRepos(orgId!) }),
  });
}

export function useDeleteRepo() {
  const orgId = useOrgStore((s) => s.activeOrgId);
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (repoId: string) => api.del(`git-repos/${repoId}`),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: queryKeys.gitRepos(orgId!) }),
  });
}
