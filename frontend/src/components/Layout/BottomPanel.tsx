import { useEffect, useRef } from "react";
import { usePanelStore, type BottomPanelView } from "../../stores/panelStore";
import { useOutputStore } from "../../stores/outputStore";
import { useAgentRuntimeStore } from "../../stores/agentRuntimeStore";
import { usePendingApprovals, useApprove, useDecline } from "../../hooks/useApprovals";
import { useIssues } from "../../hooks/useIssues";
import { useAgents } from "../../hooks/useAgents";
import { ResizeHandle } from "./ResizeHandle";

const TABS: { key: BottomPanelView; label: string }[] = [
  { key: "output", label: "Output" },
  { key: "tasks", label: "Tasks" },
  { key: "approvals", label: "Approvals" },
  { key: "problems", label: "Problems" },
];

export function BottomPanel() {
  const { bottomOpen, bottomView, sizes, resizeBottom, setBottomView, toggleBottom } = usePanelStore();

  if (!bottomOpen) return null;

  return (
    <>
      <ResizeHandle
        direction="vertical"
        onResize={(delta) => resizeBottom(sizes.bottomHeight - delta)}
      />
      <div
        className="bg-base-200 border-t border-base-content/10 flex flex-col overflow-hidden shrink-0"
        style={{ height: sizes.bottomHeight }}
      >
        <div className="flex items-center justify-between border-b border-base-content/10 px-2 h-8 shrink-0">
          <div className="flex items-center gap-0.5">
            {TABS.map((tab) => (
              <BottomTab key={tab.key} tabKey={tab.key} label={tab.label} active={bottomView === tab.key} onClick={() => setBottomView(tab.key)} />
            ))}
          </div>
          <button onClick={toggleBottom} className="btn btn-ghost btn-xs btn-square" aria-label="Close panel">
            <svg className="w-3.5 h-3.5" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
              <path d="M6 6l8 8M14 6l-8 8" />
            </svg>
          </button>
        </div>

        <div className="flex-1 overflow-y-auto">
          {bottomView === "output" && <OutputView />}
          {bottomView === "tasks" && <TasksView />}
          {bottomView === "approvals" && <ApprovalsView />}
          {bottomView === "problems" && <ProblemsView />}
        </div>
      </div>
    </>
  );
}

function BottomTab({ tabKey, label, active, onClick }: { tabKey: string; label: string; active: boolean; onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      className={`px-2.5 py-1 text-xs rounded-t transition-colors ${
        active ? "text-base-content bg-base-100 font-medium" : "text-base-content/50 hover:text-base-content"
      }`}
    >
      {label}
    </button>
  );
}

function OutputView() {
  const channels = useOutputStore((s) => s.getChannelList());
  const activeChannelId = useOutputStore((s) => s.activeChannelId);
  const setActiveChannel = useOutputStore((s) => s.setActiveChannel);
  const activeChannel = useOutputStore((s) => s.activeChannelId ? s.channels[s.activeChannelId] : null);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [activeChannel?.entries.length]);

  if (channels.length === 0) {
    return (
      <div className="p-3">
        <p className="text-xs text-base-content/50 font-mono">
          No output channels active. Output from running agents and tasks will appear here.
        </p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      {channels.length > 1 && (
        <div className="flex items-center gap-1 px-2 py-1 border-b border-base-content/5">
          <select
            className="select select-xs select-bordered text-xs"
            value={activeChannelId || ""}
            onChange={(e) => setActiveChannel(e.target.value)}
          >
            {channels.map((ch) => (
              <option key={ch.id} value={ch.id}>{ch.label}</option>
            ))}
          </select>
        </div>
      )}
      <div ref={scrollRef} className="flex-1 overflow-y-auto p-2 font-mono text-xs">
        {activeChannel?.entries.map((entry, i) => (
          <div key={i} className={`py-0.5 ${
            entry.level === "error" ? "text-error" :
            entry.level === "warn" ? "text-warning" :
            entry.level === "debug" ? "text-base-content/40" :
            "text-base-content/70"
          }`}>
            <span className="text-base-content/30 mr-2">
              {new Date(entry.timestamp).toLocaleTimeString()}
            </span>
            {entry.text}
          </div>
        ))}
      </div>
    </div>
  );
}

function TasksView() {
  const runtimeAgents = useAgentRuntimeStore((s) => s.agents);
  const { data: agents = [] } = useAgents();

  const allTasks = Object.entries(runtimeAgents).flatMap(([agentId, runtime]) =>
    runtime.runningTasks.map((task) => ({
      ...task,
      agentName: agents.find((a) => a.id === agentId)?.name || agentId,
      duration: Date.now() - task.startedAt,
    }))
  );

  if (allTasks.length === 0) {
    return (
      <div className="p-3">
        <p className="text-xs text-base-content/50">No running tasks.</p>
      </div>
    );
  }

  return (
    <div className="p-2">
      <table className="table table-xs w-full">
        <thead>
          <tr className="text-base-content/50">
            <th>Agent</th>
            <th>Task</th>
            <th>Duration</th>
          </tr>
        </thead>
        <tbody>
          {allTasks.map((task) => (
            <tr key={task.path}>
              <td className="text-xs">{task.agentName}</td>
              <td className="text-xs">{task.title}</td>
              <td className="text-xs text-base-content/50">{formatDuration(task.duration)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function ApprovalsView() {
  const { data: approvals = [] } = usePendingApprovals();
  const approveMutation = useApprove();
  const declineMutation = useDecline();

  if (approvals.length === 0) {
    return (
      <div className="p-3">
        <p className="text-xs text-base-content/50">No pending approvals.</p>
      </div>
    );
  }

  return (
    <div className="p-2 space-y-2">
      {approvals.map((a) => (
        <div key={a.task_path} className="flex items-center justify-between gap-2 p-2 bg-base-100 rounded text-xs">
          <div className="min-w-0">
            <p className="font-medium truncate">{a.title}</p>
            <p className="text-base-content/50">{a.delegated_by}</p>
          </div>
          <div className="flex gap-1 shrink-0">
            <button onClick={() => approveMutation.mutate(a.task_path)} className="btn btn-success btn-xs">Approve</button>
            <button onClick={() => declineMutation.mutate({ taskPath: a.task_path })} className="btn btn-ghost btn-xs">Decline</button>
          </div>
        </div>
      ))}
    </div>
  );
}

function ProblemsView() {
  const { data: issues = [] } = useIssues();
  const openIssues = issues.filter((i) => i.status === "open");

  if (openIssues.length === 0) {
    return (
      <div className="p-3">
        <p className="text-xs text-base-content/50">No problems detected.</p>
      </div>
    );
  }

  return (
    <div className="p-2 space-y-1">
      {openIssues.slice(0, 20).map((issue) => (
        <div key={issue.id} className="flex items-center gap-2 p-1.5 text-xs">
          <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${
            issue.priority === "p0" ? "bg-error" :
            issue.priority === "p1" ? "bg-warning" : "bg-info"
          }`} />
          <span className="truncate">{issue.name}</span>
          <span className="text-base-content/40 shrink-0">{issue.assignee}</span>
        </div>
      ))}
    </div>
  );
}

function formatDuration(ms: number): string {
  const s = Math.floor(ms / 1000);
  if (s < 60) return `${s}s`;
  const m = Math.floor(s / 60);
  return `${m}m ${s % 60}s`;
}
