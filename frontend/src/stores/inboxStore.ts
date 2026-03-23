import { create } from "zustand";
import { orgApiPath } from "./orgStore";
import { useAgentStore } from "./agentStore";

export type InboxItemType = "task_completed" | "plan_ready" | "task_failed" | "plan_declined";
export type InboxItemStatus = "pending" | "read" | "actioned";

export interface InboxItem {
  filename: string;
  agent_id: string;
  date: string;
  from: string;
  status: InboxItemStatus;
  type: InboxItemType;
  task_ref: string;
  content: string;
}

interface InboxStore {
  items: InboxItem[];
  loading: boolean;
  fetchAll: () => Promise<void>;
  markAsRead: (agentId: string, filename: string) => Promise<boolean>;
}

export const useInboxStore = create<InboxStore>((set, get) => ({
  items: [],
  loading: false,

  fetchAll: async () => {
    set({ loading: true });
    try {
      const agents = useAgentStore.getState().agents;
      const allItems: InboxItem[] = [];

      await Promise.all(
        agents
          .filter((a) => a.id !== "axon")
          .map(async (agent) => {
            try {
              const listRes = await fetch(
                orgApiPath(`vaults/${agent.id}/files?branch=inbox`)
              );
              if (!listRes.ok) return;
              const listData = await listRes.json();
              const files: { name: string }[] = listData.files || [];

              await Promise.all(
                files
                  .filter((f) => f.name.endsWith(".md"))
                  .map(async (file) => {
                    try {
                      const detailRes = await fetch(
                        orgApiPath(`vaults/${agent.id}/files/inbox/${file.name}`)
                      );
                      if (!detailRes.ok) return;
                      const detail = await detailRes.json();
                      const fm = detail.frontmatter || {};
                      allItems.push({
                        filename: file.name,
                        agent_id: agent.id,
                        date: fm.date || "",
                        from: fm.from || agent.id,
                        status: fm.status || "pending",
                        type: fm.type || "task_completed",
                        task_ref: fm.task_ref || "",
                        content: detail.content || "",
                      });
                    } catch { /* skip individual file errors */ }
                  })
              );
            } catch { /* skip agent-level errors */ }
          })
      );

      // Sort newest first
      allItems.sort((a, b) => b.date.localeCompare(a.date));
      set({ items: allItems, loading: false });
    } catch {
      set({ loading: false });
    }
  },

  markAsRead: async (agentId: string, filename: string) => {
    try {
      const item = get().items.find(
        (i) => i.agent_id === agentId && i.filename === filename
      );
      if (!item) return false;

      const res = await fetch(
        orgApiPath(`vaults/${agentId}/files/inbox/${filename}`),
        {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            content: item.content,
            frontmatter: {
              date: item.date,
              from: item.from,
              status: "read",
              type: item.type,
              task_ref: item.task_ref,
            },
          }),
        }
      );

      if (res.ok) {
        set({
          items: get().items.map((i) =>
            i.agent_id === agentId && i.filename === filename
              ? { ...i, status: "read" }
              : i
          ),
        });
        return true;
      }
      return false;
    } catch {
      return false;
    }
  },
}));
