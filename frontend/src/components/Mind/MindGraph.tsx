import { useCallback, useEffect, useMemo, useRef } from "react";
import {
  ReactFlow,
  Background,
  Controls,
  type Node,
  type Edge,
  type NodeTypes,
  Handle,
  Position,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import {
  forceSimulation,
  forceLink,
  forceManyBody,
  forceCenter,
  forceCollide,
  type SimulationNodeDatum,
  type SimulationLinkDatum,
} from "d3-force";
import type { GraphNode, GraphEdge } from "../../stores/mindStore";

const BRANCH_COLORS: Record<string, string> = {
  decisions: "#8b5cf6",
  learnings: "#06b6d4",
  contacts: "#10b981",
  hindsight: "#f59e0b",
  ideas: "#ec4899",
  tasks: "#3b82f6",
  issues: "#ef4444",
  achievements: "#22c55e",
  audit: "#6b7280",
  "": "#9ca3af",
  root: "#9ca3af",
};

function getBranchColor(branch: string): string {
  return BRANCH_COLORS[branch] || "#7c3aed";
}

interface VaultNodeData extends Record<string, unknown> {
  graphNode: GraphNode;
  isHighlighted: boolean;
  isNeighbor: boolean;
  isDimmed: boolean;
  onHover: (id: string | null) => void;
  onClick: (id: string) => void;
}

function VaultNode({ data }: { data: VaultNodeData }) {
  const { graphNode, isHighlighted, isNeighbor, isDimmed, onHover, onClick } = data;
  const connections = graphNode.linkCount + graphNode.backlinkCount;
  const size = Math.max(24, Math.min(48, 20 + connections * 4));
  const color = getBranchColor(graphNode.branch);

  return (
    <div
      className="flex flex-col items-center cursor-pointer"
      onMouseEnter={() => onHover(graphNode.id)}
      onMouseLeave={() => onHover(null)}
      onClick={() => onClick(graphNode.id)}
      style={{ opacity: isDimmed ? 0.15 : 1, transition: "opacity 150ms" }}
    >
      <Handle type="target" position={Position.Top} className="!bg-transparent !border-0 !w-0 !h-0" />
      <div
        className="rounded-full flex items-center justify-center text-xs font-bold text-white"
        style={{
          width: size,
          height: size,
          backgroundColor: color,
          boxShadow: isHighlighted
            ? `0 0 0 3px #fff, 0 0 12px ${color}`
            : isNeighbor
              ? `0 0 0 2px ${color}80`
              : "none",
          transition: "box-shadow 150ms",
        }}
      >
        {graphNode.name[0]?.toUpperCase()}
      </div>
      <span
        className="text-[10px] mt-1 max-w-[80px] truncate text-center"
        style={{
          color: isHighlighted || isNeighbor ? "#e5e7eb" : "#9ca3af",
        }}
      >
        {graphNode.title || graphNode.name}
      </span>
      <Handle type="source" position={Position.Bottom} className="!bg-transparent !border-0 !w-0 !h-0" />
    </div>
  );
}

const nodeTypes: NodeTypes = { vault: VaultNode };

interface SimNode extends SimulationNodeDatum {
  id: string;
}

interface Props {
  nodes: GraphNode[];
  edges: GraphEdge[];
  visibleBranches: Set<string>;
  highlightedNodeId: string | null;
  onNodeSelect: (id: string) => void;
  onNodeHover: (id: string | null) => void;
}

export function MindGraph({ nodes, edges, visibleBranches, highlightedNodeId, onNodeSelect, onNodeHover }: Props) {
  const layoutRef = useRef<Map<string, { x: number; y: number }>>(new Map());
  const prevNodeCountRef = useRef(0);

  // Filter nodes by visible branches
  const filteredNodes = useMemo(
    () => nodes.filter((n) => visibleBranches.has(n.branch || "root")),
    [nodes, visibleBranches],
  );

  const filteredNodeIds = useMemo(() => new Set(filteredNodes.map((n) => n.id)), [filteredNodes]);

  const filteredEdges = useMemo(
    () => edges.filter((e) => filteredNodeIds.has(e.source) && filteredNodeIds.has(e.target)),
    [edges, filteredNodeIds],
  );

  // Build neighbor set for highlighting
  const neighborIds = useMemo(() => {
    if (!highlightedNodeId) return new Set<string>();
    const ids = new Set<string>();
    for (const e of filteredEdges) {
      if (e.source === highlightedNodeId) ids.add(e.target);
      if (e.target === highlightedNodeId) ids.add(e.source);
    }
    return ids;
  }, [highlightedNodeId, filteredEdges]);

  // Run force simulation when nodes change
  useEffect(() => {
    if (filteredNodes.length === 0) return;
    if (filteredNodes.length === prevNodeCountRef.current && layoutRef.current.size > 0) return;
    prevNodeCountRef.current = filteredNodes.length;

    const simNodes: SimNode[] = filteredNodes.map((n) => ({
      id: n.id,
      x: layoutRef.current.get(n.id)?.x ?? Math.random() * 800,
      y: layoutRef.current.get(n.id)?.y ?? Math.random() * 600,
    }));

    const nodeIndex = new Map(simNodes.map((n, i) => [n.id, i]));
    const simLinks: SimulationLinkDatum<SimNode>[] = filteredEdges
      .filter((e) => nodeIndex.has(e.source) && nodeIndex.has(e.target))
      .map((e) => ({ source: nodeIndex.get(e.source)!, target: nodeIndex.get(e.target)! }));

    const sim = forceSimulation(simNodes)
      .force("link", forceLink(simLinks).distance(120).strength(0.3))
      .force("charge", forceManyBody().strength(-200))
      .force("center", forceCenter(400, 300))
      .force("collide", forceCollide(40))
      .stop();

    // Run synchronously
    for (let i = 0; i < 200; i++) sim.tick();

    const next = new Map<string, { x: number; y: number }>();
    for (const n of simNodes) {
      next.set(n.id, { x: n.x ?? 0, y: n.y ?? 0 });
    }
    layoutRef.current = next;
  }, [filteredNodes, filteredEdges]);

  // Build xyflow nodes/edges
  const flowNodes: Node[] = useMemo(() => {
    return filteredNodes.map((n) => {
      const pos = layoutRef.current.get(n.id) || { x: Math.random() * 800, y: Math.random() * 600 };
      const isHighlighted = n.id === highlightedNodeId;
      const isNeighbor = neighborIds.has(n.id);
      const isDimmed = !!highlightedNodeId && !isHighlighted && !isNeighbor;

      return {
        id: n.id,
        type: "vault",
        position: pos,
        data: {
          graphNode: n,
          isHighlighted,
          isNeighbor,
          isDimmed,
          onHover: onNodeHover,
          onClick: onNodeSelect,
        } satisfies VaultNodeData,
      };
    });
  }, [filteredNodes, highlightedNodeId, neighborIds, onNodeSelect, onNodeHover]);

  const flowEdges: Edge[] = useMemo(() => {
    return filteredEdges.map((e, i) => {
      const isActive =
        highlightedNodeId &&
        (e.source === highlightedNodeId || e.target === highlightedNodeId);
      return {
        id: `e-${i}`,
        source: e.source,
        target: e.target,
        style: {
          stroke: isActive ? "#8b5cf6" : "#374151",
          strokeWidth: isActive ? 2 : 1,
          opacity: highlightedNodeId && !isActive ? 0.1 : 0.6,
        },
      };
    });
  }, [filteredEdges, highlightedNodeId]);

  const onPaneClick = useCallback(() => {
    onNodeHover(null);
  }, [onNodeHover]);

  if (filteredNodes.length === 0) {
    return (
      <div className="h-full flex items-center justify-center text-neutral-content text-sm">
        No vault files to display
      </div>
    );
  }

  return (
    <ReactFlow
      nodes={flowNodes}
      edges={flowEdges}
      nodeTypes={nodeTypes}
      onPaneClick={onPaneClick}
      fitView
      minZoom={0.2}
      maxZoom={3}
      proOptions={{ hideAttribution: true }}
      style={{ background: "var(--color-base-100)" }}
    >
      <Background color="var(--color-base-300)" gap={24} />
      <Controls
        style={{
          background: "var(--color-base-200)",
          borderColor: "var(--color-neutral)",
        }}
      />
    </ReactFlow>
  );
}
