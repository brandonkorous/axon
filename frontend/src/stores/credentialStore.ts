import { create } from "zustand";
import { orgApiPath } from "./orgStore";

export interface Credential {
  id: string;
  provider: string;
  label: string;
  token_preview: string;
  created_at: string | null;
}

interface CredentialStore {
  credentials: Credential[];
  loading: boolean;
  fetchCredentials: () => Promise<void>;
  createCredential: (
    provider: string,
    accessToken: string,
    label?: string,
  ) => Promise<boolean>;
  deleteCredential: (credentialId: string) => Promise<boolean>;
}

export const useCredentialStore = create<CredentialStore>((set, get) => ({
  credentials: [],
  loading: false,

  fetchCredentials: async () => {
    set({ loading: true });
    try {
      const res = await fetch(orgApiPath("credentials"));
      if (!res.ok) throw new Error();
      const data = await res.json();
      set({ credentials: data, loading: false });
    } catch {
      set({ loading: false });
    }
  },

  createCredential: async (provider, accessToken, label) => {
    try {
      const res = await fetch(orgApiPath("credentials"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          provider,
          access_token: accessToken,
          label: label || "",
        }),
      });
      if (!res.ok) return false;
      await get().fetchCredentials();
      return true;
    } catch {
      return false;
    }
  },

  deleteCredential: async (credentialId) => {
    try {
      const res = await fetch(orgApiPath(`credentials/${credentialId}`), {
        method: "DELETE",
      });
      if (!res.ok) return false;
      await get().fetchCredentials();
      return true;
    } catch {
      return false;
    }
  },
}));
