import { Link } from "react-router-dom";
import { useAgentStore } from "../../stores/agentStore";
import { useAgentRuntimeStore } from "../../stores/agentRuntimeStore";
import { StatusBadge } from "../AgentControls/AgentControls";
import { StatusBarPopover } from "./StatusBarPopover";

function Dot({ color, pulse }: { color: string; pulse?: boolean }) {
    return (
        <span
            className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${color}${pulse ? " animate-pulse motion-reduce:animate-none" : ""}`}
        />
    );
}

export function StatusBarAgents({
    activeCount,
    thinkingCount,
}: {
    activeCount: number;
    thinkingCount: number;
}) {
    const agents = useAgentStore((s) => s.agents);
    const { lifecycleAction } = useAgentStore();
    const runtimeAgents = useAgentRuntimeStore((s) => s.agents);

    const visible = agents.filter((a) => a.id !== "axon" && a.type !== "external");

    return (
        <StatusBarPopover
            label={`${activeCount} active agents${thinkingCount > 0 ? `, ${thinkingCount} thinking` : ""}`}
            trigger={
                <>
                    <Dot
                        color={activeCount > 0 ? "bg-success" : "bg-neutral/50"}
                        pulse={thinkingCount > 0}
                    />
                    <span>{activeCount}</span>
                    <span className="hidden sm:inline">
                        {activeCount === 1 ? "Agent" : "Agents"}
                    </span>
                </>
            }
        >
            <div className="flex items-center justify-between px-3 py-2 border-b border-base-content/10">
                <span className="text-xs font-medium text-base-content">Agents</span>
                <Link to="/dashboard" className="text-xs text-primary hover:underline">
                    Dashboard
                </Link>
            </div>

            <ul className="overflow-y-auto flex-1 p-1 space-y-0.5">
                {visible.length === 0 && (
                    <li className="px-3 py-3 text-xs text-base-content/50 text-center">
                        No agents configured
                    </li>
                )}
                {visible.map((agent) => {
                    const status = agent.lifecycle?.status ?? "active";
                    const thinking = runtimeAgents[agent.id]?.thinking;

                    return (
                        <li
                            key={agent.id}
                            className="flex flex-row items-center justify-between gap-2 px-3 py-1.5 rounded-lg hover:bg-base-300 transition-colors"
                        >
                            <Link
                                to={`/agent/${agent.id}`}
                                className="flex items-center gap-2 min-w-0 flex-1"
                            >
                                <span
                                    className={`w-2 h-2 rounded-full flex-shrink-0${thinking ? " animate-pulse" : ""}`}
                                    style={{ backgroundColor: agent.ui.color }}
                                />
                                <span className="text-sm text-base-content truncate">
                                    {agent.name}
                                </span>
                                <StatusBadge status={status} />
                            </Link>

                            <div className="flex gap-1 flex-shrink-0">
                                {status === "active" && (
                                    <button
                                        onClick={() => lifecycleAction(agent.id, "pause")}
                                        className="btn btn-warning btn-soft btn-xs"
                                    >
                                        Pause
                                    </button>
                                )}
                                {status === "paused" && (
                                    <button
                                        onClick={() => lifecycleAction(agent.id, "resume")}
                                        className="btn btn-success btn-soft btn-xs"
                                    >
                                        Resume
                                    </button>
                                )}
                                {status === "disabled" && (
                                    <button
                                        onClick={() => lifecycleAction(agent.id, "enable")}
                                        className="btn btn-success btn-soft btn-xs"
                                    >
                                        Enable
                                    </button>
                                )}
                            </div>
                        </li>
                    );
                })}
            </ul>
        </StatusBarPopover>
    );
}
