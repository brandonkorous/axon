import { useState } from "react";
import { useAgentStore, AgentInfo, LifecycleState } from "../../stores/agentStore";
import { PersonaEditor } from "./PersonaEditor";

const STATUS_VARIANT: Record<string, string> = {
  active: "badge-success",
  paused: "badge-warning",
  disabled: "badge-ghost",
  terminated: "badge-error",
};

const STATUS_LABEL: Record<string, string> = {
  active: "Active",
  paused: "Paused",
  disabled: "Disabled",
  terminated: "Terminated",
};

export function StatusBadge({ status }: { status: string }) {
  const variant = STATUS_VARIANT[status] || "badge-success";
  const label = STATUS_LABEL[status] || status;
  return (
    <span className={`badge badge-soft badge-xs ${variant}`}>{label}</span>
  );
}

export function AgentControls({
  agentId,
  lifecycle,
  agent,
}: {
  agentId: string;
  lifecycle: LifecycleState;
  agent?: AgentInfo;
}) {
  const { lifecycleAction, deleteAgent } = useAgentStore();
  const [showStrategy, setShowStrategy] = useState(false);
  const [showPersona, setShowPersona] = useState(false);
  const [strategyPrompt, setStrategyPrompt] = useState(
    lifecycle.strategy_override || ""
  );
  const [confirmTerminate, setConfirmTerminate] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);

  const isTerminated = lifecycle.status === "terminated";

  return (
    <div className="bg-base-200 border border-neutral rounded-lg p-4 space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-base-content/60">
          Agent Controls
        </h3>
        <StatusBadge status={lifecycle.status} />
      </div>

      {!isTerminated && (
        <div className="flex flex-wrap gap-2">
          {lifecycle.status === "active" && (
            <button
              onClick={() => lifecycleAction(agentId, "pause")}
              className="btn btn-soft btn-warning btn-xs"
            >
              Pause
            </button>
          )}
          {lifecycle.status === "paused" && (
            <button
              onClick={() => lifecycleAction(agentId, "resume")}
              className="btn btn-soft btn-success btn-xs"
            >
              Resume ({lifecycle.queued_messages} queued)
            </button>
          )}
          {lifecycle.status === "active" && (
            <button
              onClick={() => lifecycleAction(agentId, "disable")}
              className="btn btn-soft btn-ghost btn-xs"
            >
              Disable
            </button>
          )}
          {lifecycle.status === "disabled" && (
            <button
              onClick={() => lifecycleAction(agentId, "enable")}
              className="btn btn-soft btn-success btn-xs"
            >
              Enable
            </button>
          )}
          <button
            onClick={() => {
              setShowStrategy(!showStrategy);
              if (!showStrategy) {
                setShowPersona(false);
              }
            }}
            className="btn btn-soft btn-accent btn-xs"
          >
            {lifecycle.strategy_override ? "Edit Strategy" : "Set Strategy"}
          </button>
          <button
            onClick={() => {
              setShowPersona(!showPersona);
              if (!showPersona) {
                setShowStrategy(false);
              }
            }}
            className="btn btn-soft btn-info btn-xs"
          >
            Edit Persona
          </button>
          {!confirmTerminate ? (
            <button
              onClick={() => setConfirmTerminate(true)}
              className="btn btn-soft btn-error btn-xs"
            >
              Terminate
            </button>
          ) : (
            <span className="flex items-center gap-1">
              <span className="text-xs text-error">Terminate this agent?</span>
              <button
                onClick={() => {
                  lifecycleAction(agentId, "terminate");
                  setConfirmTerminate(false);
                }}
                className="btn btn-error btn-xs"
              >
                Terminate
              </button>
              <button
                onClick={() => setConfirmTerminate(false)}
                className="btn btn-ghost btn-xs"
              >
                Cancel
              </button>
            </span>
          )}
        </div>
      )}

      {isTerminated && (
        <div className="flex items-center gap-3">
          <p className="text-xs text-error">
            This agent has been terminated.
          </p>
          {!confirmDelete ? (
            <button
              onClick={() => setConfirmDelete(true)}
              className="btn btn-error btn-xs"
            >
              Delete Permanently
            </button>
          ) : (
            <span className="flex items-center gap-1">
              <span className="text-xs text-error font-semibold">Delete vault and all data?</span>
              <button
                onClick={() => {
                  deleteAgent(agentId);
                  setConfirmDelete(false);
                }}
                className="btn btn-error btn-xs"
              >
                Yes, Delete
              </button>
              <button
                onClick={() => setConfirmDelete(false)}
                className="btn btn-ghost btn-xs"
              >
                No
              </button>
            </span>
          )}
        </div>
      )}

      {showStrategy && !isTerminated && (
        <div className="space-y-2">
          <textarea
            value={strategyPrompt}
            onChange={(e) => setStrategyPrompt(e.target.value)}
            placeholder="Override strategy prompt... (e.g., 'Prioritize cost reduction until further notice')"
            rows={3}
            aria-label="Strategy override prompt"
            className="textarea textarea-sm w-full font-mono resize-none"
          />
          <div className="flex gap-2">
            <button
              onClick={() => {
                lifecycleAction(agentId, "strategy-override", {
                  prompt: strategyPrompt,
                });
                setShowStrategy(false);
              }}
              disabled={!strategyPrompt.trim()}
              className="btn btn-primary btn-xs"
            >
              Apply Strategy
            </button>
            {lifecycle.strategy_override && (
              <button
                onClick={() => {
                  lifecycleAction(agentId, "strategy-override-clear");
                  setStrategyPrompt("");
                  setShowStrategy(false);
                }}
                className="btn btn-ghost btn-xs"
              >
                Clear Override
              </button>
            )}
          </div>
        </div>
      )}

      {lifecycle.strategy_override && !showStrategy && (
        <div className="text-xs text-accent bg-accent/10 rounded px-2 py-1">
          Strategy: {lifecycle.strategy_override.slice(0, 100)}
          {lifecycle.strategy_override.length > 100 ? "..." : ""}
        </div>
      )}

      {showPersona && agent && !isTerminated && (
        <PersonaEditor agent={agent} onClose={() => setShowPersona(false)} />
      )}

    </div>
  );
}
