import { useCallback, useEffect, useState } from "react";
import {
  ReactFlow,
  Background,
  Controls,
  type Node,
  type Edge,
  Position,
  MarkerType,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { orgApiPath } from "../../stores/orgStore";

interface ChartNode {
  id: string;
  name: string;
  title: string;
  tagline: string;
  color: string;
  status: string;
  has_strategy_override: boolean;
}

interface ChartEdge {
  from: string;
  to: string;
  type: string;
}

interface ChartData {
  nodes: ChartNode[];
  edges: ChartEdge[];
}

const STATUS_RING: Record<string, string> = {
  active: "var(--color-success)",
  paused: "var(--color-warning)",
  disabled: "var(--color-secondary)",
  terminated: "var(--color-error)",
};

function AgentNode({ data }: { data: ChartNode }) {
  const ringColor = STATUS_RING[data.status] || STATUS_RING.active;

  return (
    <div className="card bg-base-300 border border-secondary px-4 py-3 min-w-[160px] text-center shadow-lg">
      <div
        className="w-10 h-10 rounded-full mx-auto mb-2 flex items-center justify-center text-sm font-bold text-white"
        style={{
          backgroundColor: data.color,
          boxShadow: `0 0 0 3px ${ringColor}`,
        }}
        aria-hidden="true"
      >
        {data.name[0]}
      </div>
      <div className="text-sm font-semibold text-base-content">{data.name}</div>
      <div className="text-[10px] text-base-content/60">{data.title}</div>
      {data.has_strategy_override && (
        <div className="text-[9px] text-accent mt-1">strategy override</div>
      )}
    </div>
  );
}

const nodeTypes = { agent: AgentNode };

export function OrgChartView() {
  const [chartData, setChartData] = useState<ChartData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(orgApiPath("org-chart"))
      .then((r) => r.json())
      .then((data) => {
        setChartData(data);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  const buildLayout = useCallback(() => {
    if (!chartData) return { nodes: [], edges: [] };

    const axonNode = chartData.nodes.find((n) => n.id === "axon");
    const others = chartData.nodes.filter((n) => n.id !== "axon");

    const nodes: Node[] = [];
    const centerX = 300;

    if (axonNode) {
      nodes.push({
        id: axonNode.id,
        type: "agent",
        position: { x: centerX, y: 50 },
        data: axonNode as unknown as Record<string, unknown>,
        sourcePosition: Position.Bottom,
        targetPosition: Position.Top,
      });
    }

    const spacing = 200;
    const startX = centerX - ((others.length - 1) * spacing) / 2;
    others.forEach((node, i) => {
      nodes.push({
        id: node.id,
        type: "agent",
        position: { x: startX + i * spacing, y: 250 },
        data: node as unknown as Record<string, unknown>,
        sourcePosition: Position.Top,
        targetPosition: Position.Top,
      });
    });

    const edges: Edge[] = [];
    const seen = new Set<string>();

    for (const edge of chartData.edges) {
      const key = `${edge.from}-${edge.to}`;
      if (seen.has(key)) continue;
      seen.add(key);

      edges.push({
        id: key,
        source: edge.from,
        target: edge.to,
        animated: edge.type === "can_delegate_to",
        style: { stroke: edge.type === "can_delegate_to" ? "var(--color-primary)" : "var(--color-neutral)" },
        markerEnd: { type: MarkerType.ArrowClosed, color: "var(--color-primary)" },
      });
    }

    return { nodes, edges };
  }, [chartData]);

  if (loading) {
    return (
      <div className="h-full flex items-center justify-center">
        <span className="loading loading-spinner loading-md text-primary" />
      </div>
    );
  }

  const { nodes, edges } = buildLayout();

  return (
    <div className="h-full flex flex-col">
      <div className="px-6 py-4 border-b border-neutral">
        <h1 className="text-xl font-bold text-base-content">Org Chart</h1>
        <p className="text-xs text-base-content/60">
          Agent hierarchy and delegation relationships
        </p>
      </div>
      <div className="flex-1">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          nodeTypes={nodeTypes}
          fitView
          proOptions={{ hideAttribution: true }}
          style={{ background: "var(--color-base-100)" }}
        >
          <Background color="var(--color-base-300)" gap={20} />
          <Controls style={{ background: "var(--color-base-200)", borderColor: "var(--color-neutral)" }} />
        </ReactFlow>
      </div>
    </div>
  );
}
