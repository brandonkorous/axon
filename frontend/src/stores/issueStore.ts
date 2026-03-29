import { create } from "zustand";
import { orgApiPath } from "./orgStore";

export interface IssueComment {
  author: string;
  type: string;
  created_at: string;
  body: string;
}

export interface Issue {
  path: string;
  name: string;
  type: string;
  id: number;
  assignee: string;
  status: "open" | "in_progress" | "resolved" | "closed";
  priority: "p0" | "p1" | "p2" | "p3";
  labels: string[];
  parent_issue: string;
  created_by: string;
  created_at: string;
  updated_at: string;
  body: string;
  comment_count?: number;
  comments?: IssueComment[];
}

interface IssueStore {
  issues: Issue[];
  loading: boolean;
  error: string | null;
  fetchIssues: (filters?: {
    status?: string;
    assignee?: string;
    priority?: string;
    label?: string;
  }) => Promise<void>;
  createIssue: (data: {
    title: string;
    description?: string;
    assignee?: string;
    priority?: string;
    labels?: string[];
  }) => Promise<Issue>;
  updateIssue: (
    path: string,
    data: { status?: string; assignee?: string; priority?: string }
  ) => Promise<void>;
  addComment: (issueId: number, content: string) => Promise<void>;
}

export const useIssueStore = create<IssueStore>((set, get) => ({
  issues: [],
  loading: false,
  error: null,

  fetchIssues: async (filters) => {
    set({ loading: true, error: null });
    try {
      const params = new URLSearchParams();
      if (filters?.status) params.set("status", filters.status);
      if (filters?.assignee) params.set("assignee", filters.assignee);
      if (filters?.priority) params.set("priority", filters.priority);
      if (filters?.label) params.set("label", filters.label);
      const qs = params.toString();
      const url = orgApiPath("issues") + (qs ? `?${qs}` : "");
      const res = await fetch(url);
      if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
      const raw = await res.json();
      const issues = (raw as Issue[]).map((issue) => ({
        ...issue,
        labels: Array.isArray(issue.labels)
          ? issue.labels
          : typeof issue.labels === "string"
            ? (issue.labels as string).split(",").map((l) => l.trim()).filter(Boolean)
            : [],
      }));
      set({ issues, loading: false });
    } catch (e) {
      set({ loading: false, error: (e as Error).message });
    }
  },

  createIssue: async (data) => {
    const res = await fetch(orgApiPath("issues"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    const issue = await res.json();
    get().fetchIssues();
    return issue;
  },

  updateIssue: async (path, data) => {
    const issuePath = path.startsWith("issues/") ? path.slice(7) : path;
    await fetch(orgApiPath(`issues/${issuePath}`), {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    get().fetchIssues();
  },

  addComment: async (issueId, content) => {
    await fetch(orgApiPath(`issues/${issueId}/comments`), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ content }),
    });
  },
}));
