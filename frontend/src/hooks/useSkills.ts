import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../utils/api";
import { queryKeys } from "../utils/queryKeys";
import { useOrgStore } from "../stores/orgStore";

// ── Types ──────────────────────────────────────────────────────────────────

export interface SkillInfo {
  name: string;
  description: string;
  version: string;
  author: string;
  category: string;
  icon: string;
  triggers: string[];
  auto_inject: boolean;
  is_builtin: boolean;
  methodology_preview: string;
}

export interface SkillDetail extends SkillInfo {
  methodology: string;
  agents_using: string[];
}

export interface SkillCreatePayload {
  name: string;
  description?: string;
  version?: string;
  triggers?: string[];
  auto_inject?: boolean;
  methodology?: string;
  [key: string]: unknown;
}

export interface SkillUpdatePayload {
  description?: string;
  version?: string;
  triggers?: string[];
  auto_inject?: boolean;
  methodology?: string;
  [key: string]: unknown;
}

// ── Queries ────────────────────────────────────────────────────────────────

export function useSkills() {
  const orgId = useOrgStore((s) => s.activeOrgId);
  return useQuery({
    queryKey: queryKeys.skills(orgId!),
    queryFn: () =>
      api.get<{ skills: SkillInfo[] }>("skills").then((d) => d.skills),
    enabled: !!orgId,
  });
}

export function useSkillDetail(name: string | undefined) {
  const orgId = useOrgStore((s) => s.activeOrgId);
  return useQuery({
    queryKey: [...queryKeys.skills(orgId!), name],
    queryFn: () => api.get<SkillDetail>(`skills/${name}`),
    enabled: !!orgId && !!name,
  });
}

// ── Mutations ──────────────────────────────────────────────────────────────

export function useEnableSkill() {
  const orgId = useOrgStore((s) => s.activeOrgId);
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (vars: { skillName: string; agent_id: string }) =>
      api.post(`skills/${vars.skillName}/enable`, {
        agent_id: vars.agent_id,
      }),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: queryKeys.skills(orgId!) }),
  });
}

export function useDisableSkill() {
  const orgId = useOrgStore((s) => s.activeOrgId);
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (vars: { skillName: string; agent_id: string }) =>
      api.post(`skills/${vars.skillName}/disable`, {
        agent_id: vars.agent_id,
      }),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: queryKeys.skills(orgId!) }),
  });
}

export function useCreateSkill() {
  const orgId = useOrgStore((s) => s.activeOrgId);
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: SkillCreatePayload) => api.post("skills", data),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: queryKeys.skills(orgId!) }),
  });
}

export function useUpdateSkill() {
  const orgId = useOrgStore((s) => s.activeOrgId);
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (vars: { name: string } & SkillUpdatePayload) => {
      const { name, ...body } = vars;
      return api.put(`skills/${name}`, body);
    },
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: queryKeys.skills(orgId!) }),
  });
}

export function useDeleteSkill() {
  const orgId = useOrgStore((s) => s.activeOrgId);
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (name: string) => api.del(`skills/${name}`),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: queryKeys.skills(orgId!) }),
  });
}
