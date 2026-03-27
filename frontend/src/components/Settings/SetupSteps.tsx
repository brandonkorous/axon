import { type ReactNode } from "react";

interface Credential {
  key: string;
  label: string;
}

interface SetupStepsProps {
  credentials: Credential[];
  steps: ReactNode[];
  capabilities: string[];
  note?: string;
}

export function SetupSteps({ credentials, steps, capabilities, note }: SetupStepsProps) {
  return (
    <details className="group">
      <summary className="text-xs text-primary cursor-pointer select-none hover:underline">
        Setup guide & required credentials
      </summary>
      <div className="mt-2 space-y-3 rounded-lg bg-base-200/50 p-3">
        {/* Credentials */}
        <div>
          <span className="text-[11px] font-semibold uppercase tracking-wider text-base-content/60">
            Required Credentials
          </span>
          <ul className="mt-1 space-y-0.5">
            {credentials.map((c) => (
              <li key={c.key} className="text-xs text-base-content/80">
                <code className="text-[11px] bg-base-300/60 px-1 py-0.5 rounded">{c.key}</code>
                <span className="text-base-content/60 ml-1.5">— {c.label}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* Steps */}
        <div>
          <span className="text-[11px] font-semibold uppercase tracking-wider text-base-content/60">
            Setup Steps
          </span>
          <ol className="mt-1 space-y-1.5 list-decimal list-inside">
            {steps.map((step, i) => (
              <li key={i} className="text-xs text-base-content/80 leading-relaxed">
                {step}
              </li>
            ))}
          </ol>
        </div>

        {/* Capabilities */}
        <div>
          <span className="text-[11px] font-semibold uppercase tracking-wider text-base-content/60">
            Capabilities
          </span>
          <ul className="mt-1 space-y-0.5">
            {capabilities.map((cap, i) => (
              <li key={i} className="text-xs text-base-content/80 flex items-start gap-1.5">
                <span className="text-primary mt-0.5">&#10003;</span> {cap}
              </li>
            ))}
          </ul>
        </div>

        {/* Note */}
        {note && (
          <p className="text-[11px] text-base-content/60 italic border-l-2 border-primary/30 pl-2">
            {note}
          </p>
        )}
      </div>
    </details>
  );
}
