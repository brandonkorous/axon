import { useState } from "react";

interface Props {
  command: string;
}

export function RunCommandBlock({ command }: Props) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(command);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="relative group">
      <pre className="bg-base-300 border border-neutral rounded-lg p-4 pr-12 text-sm font-mono text-base-content overflow-x-auto whitespace-pre-wrap break-all">
        {command}
      </pre>
      <button
        onClick={handleCopy}
        className="btn btn-ghost btn-xs absolute top-2 right-2 opacity-60 group-hover:opacity-100"
        title="Copy to clipboard"
      >
        {copied ? (
          <span className="text-success text-xs">Copied</span>
        ) : (
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} className="w-4 h-4">
            <rect x="9" y="9" width="13" height="13" rx="2" />
            <path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1" />
          </svg>
        )}
      </button>
    </div>
  );
}
