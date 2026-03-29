import { create } from "zustand";
import { orgApiPath } from "./orgStore";

export interface Task {
  path: string;
  name: string;
  type: string;
  assignee: string;
  status: "pending" | "in_progress" | "done" | "blocked";
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
}

interface TaskStore {
  tasks: Task[];
  loading: boolean;
  error: string | null;
  fetchTasks: (filters?: {
    status?: string;
    assignee?: string;
    priority?: string;
  }) => Promise<void>;
  createTask: (data: {
    title: string;
    description?: string;
    assignee?: string;
    priority?: string;
    due_date?: string;
    start_date?: string;
    estimated_hours?: number | null;
    labels?: string[];
  }) => Promise<Task>;
  updateTask: (
    path: string,
    data: {
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
  ) => Promise<void>;
}

export const useTaskStore = create<TaskStore>((set, get) => ({
  tasks: [],
  loading: false,
  error: null,

  fetchTasks: async (filters) => {
    set({ loading: true, error: null });
    try {
      const params = new URLSearchParams();
      if (filters?.status) params.set("status", filters.status);
      if (filters?.assignee) params.set("assignee", filters.assignee);
      if (filters?.priority) params.set("priority", filters.priority);
      const qs = params.toString();
      const url = orgApiPath("tasks") + (qs ? `?${qs}` : "");
      const res = await fetch(url);
      if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
      const tasks = await res.json();
      set({ tasks, loading: false });
    } catch (e) {
      set({ loading: false, error: (e as Error).message });
    }
  },

  createTask: async (data) => {
    const res = await fetch(orgApiPath("tasks"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    const task = await res.json();
    // Refresh list
    get().fetchTasks();
    return task;
  },

  updateTask: async (path, data) => {
    const taskPath = path.startsWith("tasks/") ? path.slice(6) : path;
    await fetch(orgApiPath(`tasks/${taskPath}`), {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    // Refresh list
    get().fetchTasks();
  },
}));
