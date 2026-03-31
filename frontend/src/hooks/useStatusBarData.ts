import { useAgentStore } from "../stores/agentStore";
import { useAgentRuntimeStore } from "../stores/agentRuntimeStore";
import { useSandboxStore } from "../stores/sandboxStore";
import { useApprovalStore } from "../stores/approvalStore";
import { useVoiceChatStore, type VoiceState } from "../stores/voiceChatStore";

export interface StatusBarData {
  activeAgents: number;
  thinkingAgents: number;
  buildingSandboxes: number;
  pendingApprovals: number;
  voiceState: VoiceState;
}

export function useStatusBarData(): StatusBarData {
  const agents = useAgentStore((s) => s.agents);
  const runtimeAgents = useAgentRuntimeStore((s) => s.agents);
  const images = useSandboxStore((s) => s.images);
  const pendingApprovals = useApprovalStore((s) => s.approvals.length);
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
    pendingApprovals,
    voiceState,
  };
}
