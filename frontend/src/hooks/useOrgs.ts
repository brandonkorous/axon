/**
 * TanStack Query hooks for organization data.
 *
 * The orgStore stays as Zustand for client state (activeOrgId, setActiveOrg).
 * These hooks replace the fetch logic (fetchOrgs, fetchTemplates, createOrg, updateOrg).
 */

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../utils/api";
import { queryKeys } from "../utils/queryKeys";

export interface OrgAgent {
  id: string;
  name: string;
  title: string;
}

export interface DiscordConfig {
  guild_id: string;
  channel_mappings: Record<string, string>;
}

export interface SlackConfig {
  channel_mappings: Record<string, string>;
}

export interface TeamsConfig {
  tenant_id: string;
  channel_mappings: Record<string, string>;
}

export interface ZoomConfig {
  channel_mappings: Record<string, string>;
}

export interface OrgComms {
  require_approval: boolean;
  email_domain: string;
  email_signature: string;
  inbound_polling: boolean;
  discord: DiscordConfig;
  slack: SlackConfig;
  teams: TeamsConfig;
  zoom: ZoomConfig;
}

export interface OrgInfo {
  id: string;
  name: string;
  description: string;
  type: string;
  comms: OrgComms;
  agents: OrgAgent[];
  agent_count: number;
  has_huddle: boolean;
}

export interface OrgTemplateAgent {
  id: string;
  name: string;
  title: string;
  tagline: string;
  color: string;
}

export interface OrgTemplate {
  id: string;
  name: string;
  description: string;
  icon: string;
  agents: OrgTemplateAgent[];
}

/** Fetch all organizations. */
export function useOrgs() {
  return useQuery({
    queryKey: queryKeys.orgs(),
    queryFn: () =>
      api.globalGet<{ orgs: OrgInfo[] }>("/api/orgs").then((d) => d.orgs),
  });
}

/** Fetch available org templates. */
export function useOrgTemplates() {
  return useQuery({
    queryKey: queryKeys.orgTemplates(),
    queryFn: () =>
      api
        .globalGet<{ templates: OrgTemplate[] }>("/api/orgs/templates")
        .then((d) => d.templates),
  });
}

/** Create a new organization. */
export function useCreateOrg() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: { id: string; name: string; template?: string }) =>
      api.globalPost<OrgInfo>("/api/orgs", data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.orgs() }),
  });
}

/** Update an organization's settings. */
export function useUpdateOrg() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      orgId,
      update,
    }: {
      orgId: string;
      update: {
        name?: string;
        description?: string;
        type?: string;
        comms?: Partial<OrgComms>;
      };
    }) =>
      fetch(`/api/orgs/${orgId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(update),
      }).then((r) => {
        if (!r.ok) throw new Error("Failed to update org");
        return r.json();
      }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.orgs() }),
  });
}
