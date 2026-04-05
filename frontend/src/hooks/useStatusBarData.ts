import { useAgents } from "./useAgents";
import { useAgentRuntimeStore } from "../stores/agentRuntimeStore";
import { useSandboxImages } from "./useSandbox";
import { usePendingApprovals } from "./useApprovals";
import { useVoiceChatStore, type VoiceState } from "../stores/voiceChatStore";

export interface StatusBarData {
  activeAgents: number;
  thinkingAgents: number;
  buildingSandboxes: number;
  pendingApprovals: number;
  voiceState: VoiceState;
}

export function useStatusBarData(): StatusBarData {
  const { data: agents = [] } = useAgents();
  const runtimeAgents = useAgentRuntimeStore((s) => s.agents);
  const { data: images = [] } = useSandboxImages();
  const { data: approvals = [] } = usePendingApprovals();
  const voiceState = useVoiceChatStore((s) => s.voiceState);

  const activeAgents = agents.filter(
    (a) => a.id !== "axon" && a.type !== "external" && a.lifecycle?.status === "active",
  ).length;

  const thinkingAgents = Object.values(runtimeAgents).filter((s) => s.thinking).length;

  const buildingSandboxes = images.filter((i) => i.status === "building").length;

  return {
    activeAgents,
    thinkingAgents,
    buildingSandboxes,
    pendingApprovals: approvals.length,
    voiceState,
  };
}
