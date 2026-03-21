import { useEffect } from "react";
import { NavLink, Outlet } from "react-router-dom";
import { useAgentStore } from "../stores/agentStore";

export function Layout() {
  const { agents, fetchAgents, loading } = useAgentStore();

  useEffect(() => {
    fetchAgents();
  }, [fetchAgents]);

  const navLinkClass = ({ isActive }: { isActive: boolean }) =>
    `block px-3 py-2 rounded-lg text-sm transition-colors ${
      isActive
        ? "bg-gray-800 text-white"
        : "text-gray-400 hover:text-white hover:bg-gray-800/50"
    }`;

  return (
    <div className="flex h-screen">
      {/* Sidebar */}
      <aside className="w-64 bg-gray-900 border-r border-gray-800 flex flex-col">
        {/* Logo */}
        <div className="p-4 border-b border-gray-800">
          <h1 className="text-xl font-bold text-white tracking-tight">
            <span className="text-violet-400">⚡</span> Axon
          </h1>
          <p className="text-xs text-gray-500 mt-1">AI Command Center</p>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-3 space-y-1 overflow-y-auto">
          <NavLink to="/" className={navLinkClass} end>
            Axon
          </NavLink>
          <NavLink to="/boardroom" className={navLinkClass}>
            Boardroom
          </NavLink>
          <NavLink to="/dashboard" className={navLinkClass}>
            Dashboard
          </NavLink>

          {/* Agent List */}
          <div className="pt-4 pb-2">
            <p className="px-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">
              Agents
            </p>
          </div>

          {!loading &&
            agents
              .filter((a) => a.id !== "axon")
              .map((agent) => (
                <NavLink
                  key={agent.id}
                  to={`/agent/${agent.id}`}
                  className={navLinkClass}
                >
                  <span className="flex items-center gap-2">
                    <span
                      className="w-2 h-2 rounded-full"
                      style={{ backgroundColor: agent.ui.color }}
                    />
                    {agent.name}
                  </span>
                </NavLink>
              ))}

          {/* Memory Browser */}
          <div className="pt-4 pb-2">
            <p className="px-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">
              Memory
            </p>
          </div>
          <NavLink to="/memory" className={navLinkClass}>
            Memory Browser
          </NavLink>
        </nav>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-hidden">
        <Outlet />
      </main>
    </div>
  );
}
