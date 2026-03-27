import { MicCalibration } from "../VoiceChat/MicCalibration";
import { PlaybackSettings } from "../VoiceChat/PlaybackSettings";
import { VoiceSelector } from "../VoiceChat/VoiceSelector";

export function VoiceTab() {
  return (
    <div className="space-y-5">
      <VoiceSelector />
      <div className="divider my-0" />
      <MicCalibration />
      <div className="divider my-0" />
      <PlaybackSettings />
    </div>
  );
}
