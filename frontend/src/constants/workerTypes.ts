import type { WorkerType } from "../stores/workerStore";

export interface WorkerTypeInfo {
  id: WorkerType;
  label: string;
  description: string;
  icon: string;
  color: string;
  needsCodebase: boolean;
  needsWorkDir: boolean;
}

export const WORKER_TYPES: WorkerTypeInfo[] = [
  {
    id: "code",
    label: "Code",
    description: "Execute code changes via Claude Code CLI",
    icon: "M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z",
    color: "#8B5CF6",
    needsCodebase: true,
    needsWorkDir: false,
  },
  {
    id: "documents",
    label: "Documents",
    description: "PDF/DOCX parsing and summarization",
    icon: "M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z",
    color: "#3B82F6",
    needsCodebase: false,
    needsWorkDir: true,
  },
  {
    id: "email",
    label: "Email",
    description: "Gmail, O365, Resend read/send",
    icon: "M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z",
    color: "#EF4444",
    needsCodebase: false,
    needsWorkDir: false,
  },
  {
    id: "images",
    label: "Images",
    description: "Image analysis and manipulation",
    icon: "M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z",
    color: "#F59E0B",
    needsCodebase: false,
    needsWorkDir: true,
  },
  {
    id: "browser",
    label: "Browser",
    description: "Playwright web automation",
    icon: "M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9",
    color: "#10B981",
    needsCodebase: false,
    needsWorkDir: false,
  },
  {
    id: "shell",
    label: "Shell",
    description: "Direct command execution (no LLM)",
    icon: "M6 9l6 6 6-6",
    color: "#6B7280",
    needsCodebase: false,
    needsWorkDir: true,
  },
];

export const WORKER_TYPE_MAP = Object.fromEntries(
  WORKER_TYPES.map((t) => [t.id, t]),
) as Record<WorkerType, WorkerTypeInfo>;
