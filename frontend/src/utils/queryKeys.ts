/**
 * Query key factory — consistent, type-safe keys for TanStack Query.
 *
 * All keys are prefixed with orgId so an org switch invalidates everything.
 * Usage: queryKeys.agents(orgId) → ["org1", "agents"]
 */

export const queryKeys = {
  // Batch 1 — read-heavy
  agents: (orgId: string) => [orgId, "agents"] as const,
  agent: (orgId: string, agentId: string) => [orgId, "agents", agentId] as const,
  tasks: (orgId: string, filters?: Record<string, unknown>) =>
    filters ? ([orgId, "tasks", filters] as const) : ([orgId, "tasks"] as const),
  usage: (orgId: string) => [orgId, "usage"] as const,
  analytics: (orgId: string) => [orgId, "analytics"] as const,
  issues: (orgId: string, filters?: Record<string, unknown>) =>
    filters ? ([orgId, "issues", filters] as const) : ([orgId, "issues"] as const),

  documents: (orgId: string, filters?: Record<string, unknown>) =>
    filters ? ([orgId, "documents", filters] as const) : ([orgId, "documents"] as const),

  // Batch 2 — mutation-heavy
  plugins: (orgId: string) => [orgId, "plugins"] as const,
  pluginInstances: (orgId: string) => [orgId, "pluginInstances"] as const,
  skills: (orgId: string) => [orgId, "skills"] as const,
  credentials: (orgId: string) => [orgId, "credentials"] as const,
  models: (orgId: string) => [orgId, "models"] as const,
  gitRepos: (orgId: string) => [orgId, "gitRepos"] as const,
  hostAgents: (orgId: string) => [orgId, "hostAgents"] as const,
  calendar: (orgId: string) => [orgId, "calendar"] as const,
  approvals: (orgId: string) => [orgId, "approvals"] as const,

  // Batch 3 — WebSocket hybrid
  sandboxImages: (orgId: string) => [orgId, "sandboxImages"] as const,
  sandboxContainers: (orgId: string) => [orgId, "sandboxContainers"] as const,

  // Global (not org-scoped)
  orgs: () => ["orgs"] as const,
  orgTemplates: () => ["orgTemplates"] as const,
  preferences: () => ["preferences"] as const,
} as const;
