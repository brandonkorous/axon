/**
 * Centralized API client for Axon frontend.
 *
 * Wraps fetch() with typed methods, org-scoped paths, and error handling.
 * Used by TanStack Query hooks — not by Zustand stores directly.
 */

import { useOrgStore } from "../stores/orgStore";

export class ApiError extends Error {
  constructor(
    public status: number,
    public detail: string,
  ) {
    super(detail);
    this.name = "ApiError";
  }
}

function orgPath(path: string): string {
  const { activeOrgId } = useOrgStore.getState();
  if (!activeOrgId) {
    throw new Error("No active organization");
  }
  return `/api/orgs/${activeOrgId}/${path}`;
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    throw new ApiError(res.status, body.detail || res.statusText);
  }
  return res.json() as Promise<T>;
}

export const api = {
  /** GET an org-scoped resource. */
  async get<T>(path: string): Promise<T> {
    const res = await fetch(orgPath(path));
    return handleResponse<T>(res);
  },

  /** POST to an org-scoped resource. */
  async post<T>(path: string, body?: unknown): Promise<T> {
    const res = await fetch(orgPath(path), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
    return handleResponse<T>(res);
  },

  /** PATCH an org-scoped resource. */
  async patch<T>(path: string, body: unknown): Promise<T> {
    const res = await fetch(orgPath(path), {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    return handleResponse<T>(res);
  },

  /** PUT to an org-scoped resource. */
  async put<T>(path: string, body: unknown): Promise<T> {
    const res = await fetch(orgPath(path), {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    return handleResponse<T>(res);
  },

  /** DELETE an org-scoped resource. */
  async del<T>(path: string): Promise<T> {
    const res = await fetch(orgPath(path), { method: "DELETE" });
    return handleResponse<T>(res);
  },

  /** GET a global (non-org-scoped) resource. */
  async globalGet<T>(path: string): Promise<T> {
    const res = await fetch(path);
    return handleResponse<T>(res);
  },

  /** POST to a global (non-org-scoped) resource. */
  async globalPost<T>(path: string, body?: unknown): Promise<T> {
    const res = await fetch(path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
    return handleResponse<T>(res);
  },
};
