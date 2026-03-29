import { useAgentStore } from "../stores/agentStore";
import { useAgentRuntimeStore } from "../stores/agentRuntimeStore";
import { useWorkerStore } from "../stores/workerStore";
import { useSandboxStore } from "../stores/sandboxStore";
import { useApprovalStore } from "../stores/approvalStore";
import { useVoiceChatStore, type VoiceState } from "../stores/voiceChatStore";

export interface StatusBarData {
  activeAgents: number;
  thinkingAgents: number;
  runningWorkers: number;
  totalWorkers: number;
  buildingSandboxes: number;
  pendingApprovals: number;
  voiceState: VoiceState;
}

export function useStatusBarData(): StatusBarData {
  const agents = useAgentStore((s) => s.agents);
  const runtimeAgents = useAgentRuntimeStore((s) => s.agents);
  const workers = useWorkerStore((s) => s.workers);
  const images = useSandboxStore((s) => s.images);
  const pendingApprovals = useApprovalStore((s) => s.approvals.length);
  const voiceState = useVoiceChatStore((s) => s.voiceState);

  const activeAgents = agents.filter(
    (a) => a.id !== "axon" && a.type !== "external" && a.lifecycle?.status === "active",
  ).length;

  const thinkingAgents = Object.values(runtimeAgents).filter((s) => s.thinking).length;

  const runningWorkers = workers.filter(
    (w) => w.process_state === "running" || w.process_state === "starting",
  ).length;

  const buildingSandboxes = images.filter((i) => i.status === "building").length;

  return {
    activeAgents,
    thinkingAgents,
    runningWorkers,
    totalWorkers: workers.length,
    buildingSandboxes,
    pendingApprovals,
    voiceState,
  };
}
