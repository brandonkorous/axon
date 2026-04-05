import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../utils/api";
import { queryKeys } from "../utils/queryKeys";
import { useOrgStore } from "../stores/orgStore";

// --- Types ---

export interface TaskResponse {
  from: string;
  content: string;
  attachments: { type: string; path: string; label: string }[];
  timestamp: string;
  status?: "success" | "error";
}

export interface Task {
  path: string;
  name: string;
  type: string;
  assignee: string;
  owner: string;
  status: "pending" | "in_progress" | "done" | "blocked" | "accepted" | "closed";
  priority: "p0" | "p1" | "p2" | "p3";
  due_date: string;
  start_date: string;
  estimated_hours: number | null;
  parent_task: string;
  labels: string[];
  created_by: string;
  created_at: string;
  updated_at: string;
  body: string;
  responses: TaskResponse[];
}

export interface TaskFilters {
  status?: string;
  assignee?: string;
  priority?: string;
}

export interface CreateTaskInput {
  title: string;
  description?: string;
  assignee?: string;
  priority?: string;
  due_date?: string;
  start_date?: string;
  estimated_hours?: number | null;
  labels?: string[];
}

export interface UpdateTaskInput {
  status?: string;
  assignee?: string;
  priority?: string;
  name?: string;
  due_date?: string;
  start_date?: string;
  estimated_hours?: number | null;
  labels?: string[];
  body?: string;
}

// --- Helpers ---

function buildTaskPath(filters?: TaskFilters): string {
  const parts: string[] = [];
  if (filters?.status) parts.push(`status=${filters.status}`);
  if (filters?.assignee) parts.push(`assignee=${filters.assignee}`);
  if (filters?.priority) parts.push(`priority=${filters.priority}`);
  return parts.length ? `tasks?${parts.join("&")}` : "tasks";
}

// --- Queries ---

export function useTasks(filters?: TaskFilters) {
  const orgId = useOrgStore((s) => s.activeOrgId);
  return useQuery({
    queryKey: queryKeys.tasks(orgId, filters as Record<string, unknown> | undefined),
    queryFn: () => api.get<Task[]>(buildTaskPath(filters)),
    enabled: !!orgId,
  });
}

// --- Mutations ---

export function useCreateTask() {
  const queryClient = useQueryClient();
  const orgId = useOrgStore((s) => s.activeOrgId);
  return useMutation({
    mutationFn: (data: CreateTaskInput) => api.post<Task>("tasks", data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.tasks(orgId) });
    },
  });
}

export function useUpdateTask() {
  const queryClient = useQueryClient();
  const orgId = useOrgStore((s) => s.activeOrgId);
  return useMutation({
    mutationFn: ({ path, data }: { path: string; data: UpdateTaskInput }) => {
      const taskPath = path.startsWith("tasks/") ? path.slice(6) : path;
      return api.put(`tasks/${taskPath}`, data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.tasks(orgId) });
    },
  });
}
