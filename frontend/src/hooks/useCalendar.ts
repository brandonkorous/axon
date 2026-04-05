import { useQuery } from "@tanstack/react-query";
import { api } from "../utils/api";
import { queryKeys } from "../utils/queryKeys";
import { useOrgStore } from "../stores/orgStore";

// --- Types ---

export interface CalendarEvent {
  id: string;
  title: string;
  start_date: string;
  end_date: string;
  start_time?: string;
  end_time?: string;
  source: "task" | "scheduled_action" | "sandbox";
  agent_id?: string;
  status?: string;
  priority?: string;
  metadata?: Record<string, unknown>;
}

// --- Queries ---

export function useCalendarEvents(
  start: string,
  end: string,
  agentId?: string,
  source?: string,
) {
  const orgId = useOrgStore((s) => s.activeOrgId);
  return useQuery({
    queryKey: [...queryKeys.calendar(orgId), { start, end, agentId, source }],
    queryFn: () => {
      const params = new URLSearchParams({ start, end });
      if (agentId) params.set("agent_id", agentId);
      if (source) params.set("source", source);
      return api.get<CalendarEvent[]>(`calendar?${params.toString()}`);
    },
    enabled: !!orgId && !!start && !!end,
  });
}
