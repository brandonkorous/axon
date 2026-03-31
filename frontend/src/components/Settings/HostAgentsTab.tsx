import { useEffect, useState } from "react";
import { useHostAgentStore, type HostAgent } from "../../stores/hostAgentStore";
import { orgApiPath } from "../../stores/orgStore";

export function HostAgentsTab() {
  const { agents, loading, managerRunning, hostOrgsPath, fetchAgents, fetchManagerStatus, checkHealth } =
    useHostAgentStore();

  useEffect(() => {
    fetchManagerStatus();
    fetchAgents().then(() => {
      const { agents: current } = useHostAgentStore.getState();
      current.forEach((a) => checkHealth(a.id));
    });
  }, [fetchAgents, fetchManagerStatus, checkHealth]);

  return (
    <div className="space-y-6">
      <ManagerStatusBanner running={managerRunning} orgsPath={hostOrgsPath} />
      <div>
        <h3 className="text-sm font-semibold mb-1">Registered Host Agents</h3>
        <p className="text-xs text-base-content/60 mb-3">
          Lightweight services on your host machine providing filesystem and executable access.
        </p>
        {loading && <span className="loading loading-spinner loading-sm text-primary" />}
        {!loading && agents.length === 0 && (
          <p className="text-xs text-base-content/50 italic">No host agents registered yet.</p>
        )}
        {!loading && agents.length > 0 && (
          <HostAgentTable agents={agents} managerRunning={managerRunning} />
        )}
      </div>
      <AddHostAgentForm nextPort={nextPort(agents)} />
    </div>
  );
}

function ManagerStatusBanner({ running, orgsPath }: { running: boolean; orgsPath: string }) {
  const [regenerating, setRegenerating] = useState(false);
  const [copied, setCopied] = useState(false);

  const handleRegenerate = async () => {
    setRegenerating(true);
    try {
      await fetch(orgApiPath("host-agents/regenerate-scripts"), { method: "POST" });
    } catch { /* ignore */ }
    setRegenerating(false);
  };

  const handleCopyPath = () => {
    const p = orgsPath || "(your orgs folder)";
    navigator.clipboard.writeText(p);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (running) {
    return (
      <div className="alert alert-success py-2 text-sm">
        <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 shrink-0" viewBox="0 0 20 20" fill="currentColor">
          <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
        </svg>
        <span>Host Agent Manager is running</span>
      </div>
    );
  }

  return (
    <div className="alert alert-warning py-3 text-sm">
      <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 shrink-0" viewBox="0 0 20 20" fill="currentColor">
        <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
      </svg>
      <div className="flex flex-col gap-2">
        <span className="font-semibold">Host Agent Manager is not running</span>
        <span className="text-xs opacity-80">
          To enable host filesystem access, open your orgs folder and run the startup script:
        </span>
        {orgsPath && (
          <div className="flex items-center gap-2">
            <code className="bg-base-100/30 px-2 py-0.5 rounded text-xs">{orgsPath}</code>
            <button className="btn btn-xs btn-ghost" onClick={handleCopyPath}>
              {copied ? "Copied!" : "Copy Path"}
            </button>
          </div>
        )}
        <div className="text-xs opacity-80 space-y-0.5">
          <p><strong>Windows:</strong> Double-click <code className="bg-base-100/30 px-1 rounded">host-manager.cmd</code></p>
          <p><strong>Mac/Linux:</strong> Run <code className="bg-base-100/30 px-1 rounded">./host-manager.sh</code></p>
        </div>
        <div>
          <button
            className="btn btn-xs btn-outline"
            onClick={handleRegenerate}
            disabled={regenerating}
          >
            {regenerating ? "Regenerating..." : "Regenerate Startup Scripts"}
          </button>
        </div>
      </div>
    </div>
  );
}

function nextPort(agents: HostAgent[]): number {
  if (agents.length === 0) return 9100;
  return Math.max(...agents.map((a) => a.port)) + 1;
}

function HostAgentTable({ agents, managerRunning }: { agents: HostAgent[]; managerRunning: boolean }) {
  const { deleteAgent, startAgent, stopAgent } = useHostAgentStore();
  const [deleting, setDeleting] = useState<string | null>(null);
  const [toggling, setToggling] = useState<string | null>(null);

  const handleRemove = async (id: string) => {
    setDeleting(id);
    await deleteAgent(id);
    setDeleting(null);
  };

  const handleToggle = async (agent: HostAgent) => {
    setToggling(agent.id);
    if (agent.status === "running") {
      await stopAgent(agent.id);
    } else {
      await startAgent(agent.id);
    }
    setToggling(null);
  };

  const managerTooltip = !managerRunning ? "Start the Host Agent Manager first" : undefined;

  return (
    <div className="overflow-x-auto">
      <table className="table table-xs w-full">
        <thead>
          <tr className="text-xs text-base-content/60">
            <th>Status</th>
            <th>Name</th>
            <th>Path</th>
            <th>Port</th>
            <th>Executables</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {agents.map((a) => (
            <tr key={a.id} className="hover">
              <td>
                <span className={`inline-block w-2.5 h-2.5 rounded-full ${a.status === "running" ? "bg-success animate-pulse" : a.status === "stopped" ? "bg-error" : "bg-base-content/30"}`} title={a.status} />
              </td>
              <td className="font-medium">{a.name}</td>
              <td className="font-mono text-xs opacity-70">{a.path}</td>
              <td className="font-mono text-xs">:{a.port}</td>
              <td>
                <div className="flex flex-wrap gap-1">
                  {a.executables.map((ex) => (
                    <span key={ex} className="badge badge-xs badge-ghost">{ex}</span>
                  ))}
                </div>
              </td>
              <td className="flex gap-1">
                {a.status === "running" ? (
                  <button
                    className="btn btn-xs btn-error btn-outline"
                    onClick={() => handleToggle(a)}
                    disabled={!managerRunning || toggling === a.id}
                    title={managerTooltip}
                  >
                    {toggling === a.id ? "..." : "Stop"}
                  </button>
                ) : (
                  <button
                    className="btn btn-xs btn-success btn-outline"
                    onClick={() => handleToggle(a)}
                    disabled={!managerRunning || toggling === a.id}
                    title={managerTooltip}
                  >
                    {toggling === a.id ? "..." : "Start"}
                  </button>
                )}
                <button
                  className="btn btn-ghost btn-xs text-error"
                  onClick={() => handleRemove(a.id)}
                  disabled={deleting === a.id}
                >
                  {deleting === a.id ? "..." : "Remove"}
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function AddHostAgentForm({ nextPort }: { nextPort: number }) {
  const { registerAgent } = useHostAgentStore();
  const [name, setName] = useState("");
  const [id, setId] = useState("");
  const [path, setPath] = useState("");
  const [port, setPort] = useState(nextPort);
  const [executables, setExecutables] = useState("");
  const [saving, setSaving] = useState(false);
  const [idTouched, setIdTouched] = useState(false);

  const autoId = name
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "");

  const effectiveId = idTouched ? id : autoId;

  const handleSave = async () => {
    if (!effectiveId || !name) return;
    setSaving(true);
    const execList = executables.split(",").map((e) => e.trim()).filter(Boolean);
    const ok = await registerAgent({ id: effectiveId, name, path, port, executables: execList });
    if (ok) {
      setName("");
      setId("");
      setPath("");
      setPort(nextPort + 1);
      setExecutables("");
      setIdTouched(false);
    }
    setSaving(false);
  };

  return (
    <div className="border border-neutral rounded-lg p-4 space-y-3">
      <h3 className="text-sm font-semibold">Add Host Agent</h3>
      <div className="grid grid-cols-2 gap-3">
        <div className="form-control">
          <label className="label py-0.5"><span className="label-text text-xs">Name</span></label>
          <input
            type="text" className="input input-bordered input-sm w-full"
            placeholder="Dev Environment" value={name}
            onChange={(e) => setName(e.target.value)}
          />
        </div>
        <div className="form-control">
          <label className="label py-0.5"><span className="label-text text-xs">ID</span></label>
          <input
            type="text" className="input input-bordered input-sm w-full"
            placeholder={autoId || "dev-environment"} value={idTouched ? id : autoId}
            onChange={(e) => { setId(e.target.value); setIdTouched(true); }}
          />
        </div>
      </div>
      <div className="grid grid-cols-[1fr_auto] gap-3">
        <div className="form-control">
          <label className="label py-0.5"><span className="label-text text-xs">Path</span></label>
          <input
            type="text" className="input input-bordered input-sm w-full"
            placeholder="D:\code" value={path}
            onChange={(e) => setPath(e.target.value)}
          />
        </div>
        <div className="form-control">
          <label className="label py-0.5"><span className="label-text text-xs">Port</span></label>
          <input
            type="number" className="input input-bordered input-sm w-24"
            value={port} onChange={(e) => setPort(Number(e.target.value))}
          />
        </div>
      </div>
      <div className="form-control">
        <label className="label py-0.5"><span className="label-text text-xs">Executables (comma-separated)</span></label>
        <input
          type="text" className="input input-bordered input-sm w-full"
          placeholder="git, node, python" value={executables}
          onChange={(e) => setExecutables(e.target.value)}
        />
      </div>
      <button className="btn btn-primary btn-sm" onClick={handleSave} disabled={saving || !name}>
        {saving ? "Saving..." : "Save"}
      </button>
    </div>
  );
}

