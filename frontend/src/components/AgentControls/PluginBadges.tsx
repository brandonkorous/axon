import type { AgentInfo } from "../../stores/agentStore";

/* ------------------------------------------------------------------ */
/* Inline SVG icons (no external icon library in this project)        */
/* ------------------------------------------------------------------ */

function TerminalIcon({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" className={className}>
      <polyline points="4 17 10 11 4 5" />
      <line x1="12" y1="19" x2="20" y2="19" />
    </svg>
  );
}

function BoxIcon({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" className={className}>
      <path d="M21 16V8a2 2 0 00-1-1.73l-7-4a2 2 0 00-2 0l-7 4A2 2 0 003 8v8a2 2 0 001 1.73l7 4a2 2 0 002 0l7-4A2 2 0 0021 16z" />
      <polyline points="3.27 6.96 12 12.01 20.73 6.96" />
      <line x1="12" y1="22.08" x2="12" y2="12" />
    </svg>
  );
}

/* ------------------------------------------------------------------ */
/* Badge components                                                   */
/* ------------------------------------------------------------------ */

function formatExecs(executables: string[]): string {
  if (executables.length === 0) return "none";
  return executables.join(", ");
}

function hasShellAccess(agent: AgentInfo): boolean {
  return (
    agent.plugins?.shell_access?.enabled === true ||
    agent.plugin_names?.includes("shell_access") === true
  );
}

function hasSandbox(agent: AgentInfo): boolean {
  return (
    agent.plugins?.sandbox?.enabled === true ||
    agent.plugin_names?.includes("sandbox") === true
  );
}

/** Small badges for agent cards / list rows. */
export function PluginBadges({
  agent,
  size = "default",
}: {
  agent: AgentInfo;
  size?: "default" | "compact";
}) {
  const showShell = hasShellAccess(agent);
  const showSandbox = hasSandbox(agent);
  const shell = agent.plugins?.shell_access;
  const sandbox = agent.plugins?.sandbox;

  if (!showShell && !showSandbox) return null;

  const iconSize = size === "compact" ? "w-2.5 h-2.5" : "w-3 h-3";
  const badgeSize = size === "compact" ? "badge-xs" : "badge-sm";

  return (
    <>
      {showShell && (
        <span
          className={`badge badge-warning ${badgeSize} gap-0.5`}
          title={shell ? `Shell Access: ${shell.path}\nExecutables: ${formatExecs(shell.executables)}` : "Shell Access enabled"}
        >
          <TerminalIcon className={iconSize} />
          {size !== "compact" && <span>Shell</span>}
        </span>
      )}
      {showSandbox && (
        <span
          className={`badge badge-info ${badgeSize} gap-0.5`}
          title={sandbox ? `Sandbox: ${sandbox.path}\nImage: ${sandbox.image}\nExecutables: ${formatExecs(sandbox.executables)}` : "Sandbox enabled"}
        >
          <BoxIcon className={iconSize} />
          {size !== "compact" && <span>Sandbox</span>}
        </span>
      )}
    </>
  );
}

/** Dot-only indicator for very tight spaces (status bar rows). */
export function PluginDots({ agent }: { agent: AgentInfo }) {
  const showShell = hasShellAccess(agent);
  const showSandbox = hasSandbox(agent);

  if (!showShell && !showSandbox) return null;

  return (
    <>
      {showShell && (
        <span
          className="w-2 h-2 rounded-full bg-warning shrink-0"
          title="Shell Access enabled"
        />
      )}
      {showSandbox && (
        <span
          className="w-2 h-2 rounded-full bg-info shrink-0"
          title="Sandbox enabled"
        />
      )}
    </>
  );
}

/* ------------------------------------------------------------------ */
/* Detail section for agent settings / controls                       */
/* ------------------------------------------------------------------ */

export function PluginDetailSection({ agent }: { agent: AgentInfo }) {
  const showShell = hasShellAccess(agent);
  const showSandbox = hasSandbox(agent);
  const shell = agent.plugins?.shell_access;
  const sandbox = agent.plugins?.sandbox;

  if (!showShell && !showSandbox) return null;

  return (
    <div className="space-y-2">
      <h4 className="text-xs font-semibold text-base-content/60 uppercase tracking-wide">
        Plugins
      </h4>

      {showShell && (
        <div className="alert alert-warning text-xs py-2">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} className="w-4 h-4 shrink-0">
            <path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" />
            <line x1="12" y1="9" x2="12" y2="13" />
            <line x1="12" y1="17" x2="12.01" y2="17" />
          </svg>
          <div>
            {shell ? (
              <>
                <span>
                  This agent has direct access to your filesystem at{" "}
                  <code className="font-mono bg-warning/20 px-1 rounded">{shell.path}</code>
                </span>
                {shell.executables.length > 0 && (
                  <p className="mt-1 text-base-content/70">
                    Allowed executables:{" "}
                    <span className="font-mono">{shell.executables.join(", ")}</span>
                  </p>
                )}
              </>
            ) : (
              <span>This agent has shell access enabled.</span>
            )}
          </div>
        </div>
      )}

      {showSandbox && (
        <div className="alert alert-info text-xs py-2">
          <BoxIcon className="w-4 h-4 shrink-0" />
          <div>
            {sandbox ? (
              <>
                <span>
                  Sandbox environment at{" "}
                  <code className="font-mono bg-info/20 px-1 rounded">{sandbox.path}</code>
                </span>
                <p className="mt-1 text-base-content/70">
                  Image: <span className="font-mono">{sandbox.image}</span>
                </p>
                {sandbox.executables.length > 0 && (
                  <p className="text-base-content/70">
                    Executables:{" "}
                    <span className="font-mono">{sandbox.executables.join(", ")}</span>
                  </p>
                )}
              </>
            ) : (
              <span>This agent has a sandbox environment enabled.</span>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
