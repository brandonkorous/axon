import { useEffect, useRef } from "react";
import { useVoiceChatStore } from "../../stores/voiceChatStore";
import { MicCalibration } from "./MicCalibration";
import { PlaybackSettings } from "./PlaybackSettings";
import { VoiceSelector } from "./VoiceSelector";

export function VoiceSettingsModal() {
  const isOpen = useVoiceChatStore((s) => s.settingsOpen);
  const close = useVoiceChatStore((s) => s.closeSettings);
  const dialogRef = useRef<HTMLDialogElement>(null);

  useEffect(() => {
    if (isOpen) {
      dialogRef.current?.showModal();
    } else {
      dialogRef.current?.close();
    }
  }, [isOpen]);

  return (
    <dialog ref={dialogRef} className="modal" onClose={close}>
      <div className="modal-box max-w-sm bg-base-200 border border-neutral">
        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-semibold">Voice Settings</h3>
          <form method="dialog">
            <button className="btn btn-ghost btn-sm btn-square" aria-label="Close">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} className="w-4 h-4">
                <path d="M18 6L6 18M6 6l12 12" />
              </svg>
            </button>
          </form>
        </div>

        {/* Sections */}
        <div className="space-y-5">
          <VoiceSelector />
          <div className="divider my-0" />
          <MicCalibration />
          <div className="divider my-0" />
          <PlaybackSettings />
        </div>
      </div>

      {/* Click backdrop to close */}
      <form method="dialog" className="modal-backdrop">
        <button aria-label="Close"><span className="sr-only">close</span></button>
      </form>
    </dialog>
  );
}
