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
  parent_id?: string;
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

function AgentNode({ data }: { data: ChartNode & { isSubAgent?: boolean } }) {
  const ringColor = STATUS_RING[data.status] || STATUS_RING.active;
  const isChild = data.isSubAgent;

  return (
    <div className={`card bg-base-300 border border-secondary text-center shadow-lg ${isChild ? "px-3 py-2 min-w-[140px]" : "px-4 py-3 min-w-[160px]"}`}>
      <div
        className={`rounded-full mx-auto mb-2 flex items-center justify-center font-bold text-white ${isChild ? "w-8 h-8 text-xs" : "w-10 h-10 text-sm"}`}
        style={{
          backgroundColor: data.color,
          boxShadow: `0 0 0 3px ${ringColor}`,
        }}
        aria-hidden="true"
      >
        {data.name[0]}
      </div>
      <div className={`font-semibold text-base-content ${isChild ? "text-xs" : "text-sm"}`}>{data.name}</div>
      <div className={`text-base-content/60 ${isChild ? "text-[9px]" : "text-[10px]"}`}>{data.title}</div>
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
    const topLevel = chartData.nodes.filter((n) => n.id !== "axon" && !n.parent_id);
    const subAgents = chartData.nodes.filter((n) => n.parent_id);

    // Group sub-agents by parent
    const childrenOf = new Map<string, ChartNode[]>();
    for (const sub of subAgents) {
      const list = childrenOf.get(sub.parent_id!) || [];
      list.push(sub);
      childrenOf.set(sub.parent_id!, list);
    }

    const nodes: Node[] = [];
    const centerX = 300;
    const spacing = 200;

    // Tier 0: Axon (orchestrator)
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

    // Tier 1: top-level agents
    const startX = centerX - ((topLevel.length - 1) * spacing) / 2;
    topLevel.forEach((node, i) => {
      const x = startX + i * spacing;
      nodes.push({
        id: node.id,
        type: "agent",
        position: { x, y: 250 },
        data: node as unknown as Record<string, unknown>,
        sourcePosition: Position.Bottom,
        targetPosition: Position.Top,
      });

      // Tier 2: children of this agent
      const children = childrenOf.get(node.id) || [];
      const childSpacing = 170;
      const childStartX = x - ((children.length - 1) * childSpacing) / 2;
      children.forEach((child, j) => {
        nodes.push({
          id: child.id,
          type: "agent",
          position: { x: childStartX + j * childSpacing, y: 450 },
          data: { ...child, isSubAgent: true } as unknown as Record<string, unknown>,
          sourcePosition: Position.Bottom,
          targetPosition: Position.Top,
        });
      });
    });

    // Edges
    const edges: Edge[] = [];
    const seen = new Set<string>();

    // Separate parent_child edges from delegation edges — parent_child take priority
    const parentChildPairs = new Set<string>();
    for (const edge of chartData.edges) {
      if (edge.type === "parent_child") {
        parentChildPairs.add(`${edge.from}-${edge.to}`);
      }
    }

    for (const edge of chartData.edges) {
      const pairKey = `${edge.from}-${edge.to}`;
      const key = `${pairKey}-${edge.type}`;
      if (seen.has(key)) continue;
      seen.add(key);

      const isParentChild = edge.type === "parent_child";

      // Skip delegation edges that duplicate a parent_child relationship
      if (!isParentChild && parentChildPairs.has(pairKey)) continue;

      edges.push({
        id: key,
        source: edge.from,
        target: edge.to,
        animated: !isParentChild && edge.type === "can_delegate_to",
        style: {
          stroke: isParentChild
            ? "var(--color-secondary)"
            : edge.type === "can_delegate_to"
              ? "var(--color-primary)"
              : "var(--color-neutral)",
          strokeWidth: isParentChild ? 2 : 1,
        },
        markerEnd: {
          type: MarkerType.ArrowClosed,
          color: isParentChild ? "var(--color-secondary)" : "var(--color-primary)",
        },
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
