import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useAgentStore } from "../../stores/agentStore";

interface Decision {
  vault: string;
  path: string;
  name: string;
  description: string;
  date: string;
}

interface DashboardData {
  agents: Array<{
    id: string;
    name: string;
    title: string;
    color: string;
    status: string;
    vault_files: number;
    message_count: number;
  }>;
  recent_decisions: Decision[];
  pending_actions: Array<Record<string, unknown>>;
}

export function DashboardView() {
  const { agents } = useAgentStore();
  const [data, setData] = useState<DashboardData | null>(null);

  useEffect(() => {
    fetch("/api/dashboard")
      .then((r) => r.json())
      .then(setData)
      .catch(() => {});
  }, []);

  return (
    <div className="h-full overflow-y-auto p-6">
      <h1 className="text-2xl font-bold text-white mb-6">Command Center</h1>

      {/* Agent Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {agents
          .filter((a) => a.id !== "axon")
          .map((agent) => (
            <Link
              key={agent.id}
              to={`/agent/${agent.id}`}
              className="bg-gray-800/50 border border-gray-700/50 rounded-xl p-4 hover:bg-gray-800 transition-colors"
            >
              <div className="flex items-center gap-3 mb-3">
                <div
                  className="w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold text-white"
                  style={{ backgroundColor: agent.ui.color }}
                >
                  {agent.name[0]}
                </div>
                <div>
                  <div className="font-semibold text-white">{agent.name}</div>
                  <div className="text-xs text-gray-500">{agent.title}</div>
                </div>
              </div>
              <div className="text-xs text-gray-500">
                <span
                  className="inline-block w-2 h-2 rounded-full mr-1"
                  style={{
                    backgroundColor:
                      agent.status === "idle" ? "#6B7280" : agent.ui.color,
                  }}
                />
                {agent.status}
              </div>
            </Link>
          ))}

        {/* Boardroom card */}
        <Link
          to="/boardroom"
          className="bg-gray-800/50 border border-gray-700/50 rounded-xl p-4 hover:bg-gray-800 transition-colors"
        >
          <div className="flex items-center gap-3 mb-3">
            <div className="w-10 h-10 rounded-full bg-amber-500 flex items-center justify-center text-sm font-bold text-white">
              B
            </div>
            <div>
              <div className="font-semibold text-white">Boardroom</div>
              <div className="text-xs text-gray-500">Group Session</div>
            </div>
          </div>
          <div className="text-xs text-gray-500">All advisors</div>
        </Link>
      </div>

      {/* Recent Decisions */}
      <div className="mb-8">
        <h2 className="text-lg font-semibold text-white mb-4">Recent Decisions</h2>
        {data?.recent_decisions && data.recent_decisions.length > 0 ? (
          <div className="space-y-2">
            {data.recent_decisions.map((d, i) => (
              <div
                key={i}
                className="bg-gray-800/30 border border-gray-700/30 rounded-lg px-4 py-3"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <span className="text-sm font-medium text-white">{d.name}</span>
                    <span className="text-xs text-gray-500 ml-2">({d.vault})</span>
                  </div>
                  <span className="text-xs text-gray-500">{d.date}</span>
                </div>
                {d.description && (
                  <p className="text-xs text-gray-400 mt-1">{d.description}</p>
                )}
              </div>
            ))}
          </div>
        ) : (
          <p className="text-sm text-gray-500">No decisions recorded yet.</p>
        )}
      </div>

      {/* Pending Actions */}
      <div>
        <h2 className="text-lg font-semibold text-white mb-4">Pending Actions</h2>
        {data?.pending_actions && data.pending_actions.length > 0 ? (
          <div className="space-y-2">
            {data.pending_actions.map((action, i) => (
              <div
                key={i}
                className="bg-gray-800/30 border border-gray-700/30 rounded-lg px-4 py-3 text-sm text-gray-300"
              >
                {JSON.stringify(action)}
              </div>
            ))}
          </div>
        ) : (
          <p className="text-sm text-gray-500">No pending actions.</p>
        )}
      </div>
    </div>
  );
}
