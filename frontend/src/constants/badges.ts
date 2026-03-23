/** DaisyUI badge variant classes for priority levels. */
export const PRIORITY_BADGE: Record<string, string> = {
  p0: "badge-error",
  p1: "badge-warning",
  p2: "badge-info",
  p3: "badge-ghost",
};

/** DaisyUI badge variant classes for task/issue status. */
export const STATUS_BADGE: Record<string, string> = {
  pending: "badge-warning",
  in_progress: "badge-info",
  done: "badge-success",
  blocked: "badge-error",
  open: "badge-warning",
  resolved: "badge-success",
  closed: "badge-ghost",
};
