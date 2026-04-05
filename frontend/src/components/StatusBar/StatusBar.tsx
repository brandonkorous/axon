import { useStatusBarData } from "../../hooks/useStatusBarData";
import { useVoiceChatStore } from "../../stores/voiceChatStore";
import type { VoiceState } from "../../stores/voiceChatStore";
import { StatusBarAgents } from "./StatusBarAgents";
import { StatusBarSandboxes } from "./StatusBarSandboxes";
import { StatusBarApprovals } from "./StatusBarApprovals";
import { StatusBarUsage } from "./StatusBarUsage";
import { StatusBarOrg } from "./StatusBarOrg";

const VOICE_DOT: Record<VoiceState, string> = {
  idle: "bg-neutral/50",
  listening: "bg-success",
  processing: "bg-warning",
  speaking: "bg-info",
};

const VOICE_LABEL: Record<VoiceState, string> = {
  idle: "Voice",
  listening: "Listening",
  processing: "Processing",
  speaking: "Speaking",
};

export function StatusBar() {
  const data = useStatusBarData();
  const openVoice = useVoiceChatStore((s) => s.open);

  return (
    <footer
      role="status"
      className="bg-base-200 border-t border-base-content/10 h-7 flex-shrink-0"
    >
      <div className="flex items-center justify-between h-full px-1 text-xs select-none">
        {/* Left cluster */}
        <div className="flex items-center h-full">
          <StatusBarOrg />
          <StatusBarAgents
            activeCount={data.activeAgents}
            thinkingCount={data.thinkingAgents}
          />
          <StatusBarSandboxes buildingCount={data.buildingSandboxes} />
        </div>

        {/* Right cluster */}
        <div className="flex items-center h-full">
          <button
            onClick={openVoice}
            className="px-2.5 h-full flex items-center gap-1.5 bg-primary text-primary-content hover:brightness-110 transition-all focus-visible:outline focus-visible:outline-primary-content animate-voice-glow"
            aria-label={`Voice: ${data.voiceState}`}
          >
            <span
              className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${data.voiceState === "idle" ? "bg-primary-content/50" : VOICE_DOT[data.voiceState]}${data.voiceState !== "idle" ? " animate-pulse motion-reduce:animate-none" : ""}`}
            />
            <span className="hidden sm:inline">
              {VOICE_LABEL[data.voiceState]}
            </span>
          </button>

          <StatusBarApprovals count={data.pendingApprovals} />
          <StatusBarUsage />
        </div>
      </div>
    </footer>
  );
}
