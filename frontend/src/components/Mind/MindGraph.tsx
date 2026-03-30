import { useEffect, useMemo, useRef } from "react";
import * as echarts from "echarts/core";
import { GraphChart } from "echarts/charts";
import { TooltipComponent, LegendComponent } from "echarts/components";
import { CanvasRenderer } from "echarts/renderers";
import type { GraphNode, GraphEdge } from "../../stores/mindStore";

echarts.use([GraphChart, TooltipComponent, LegendComponent, CanvasRenderer]);

const BRANCH_COLORS: Record<string, string> = {
  decisions: "#f97316",
  learnings: "#06b6d4",
  contacts: "#10b981",
  hindsight: "#a855f7",
  ideas: "#ec4899",
  tasks: "#3b82f6",
  issues: "#ef4444",
  achievements: "#22c55e",
  audit: "#6b7280",
  memory: "#f59e0b",
  conversations: "#9ca3af",
  deep: "#9ca3af",
  research: "#8b5cf6",
  branding: "#d946ef",
  inbox: "#0ea5e9",
  "": "#9ca3af",
  root: "#9ca3af",
};

// Fallback palette for branches not in the map
const FALLBACK_COLORS = ["#f59e0b", "#14b8a6", "#a855f7", "#f43f5e", "#84cc16", "#0891b2", "#e879f9", "#fb923c"];

function getBranchColor(branch: string): string {
  if (BRANCH_COLORS[branch]) return BRANCH_COLORS[branch];
  // Deterministic color from branch name so it's stable across renders
  let hash = 0;
  for (let i = 0; i < branch.length; i++) hash = (hash * 31 + branch.charCodeAt(i)) | 0;
  return FALLBACK_COLORS[Math.abs(hash) % FALLBACK_COLORS.length];
}

const LABEL_SIZE_THRESHOLD = 25;

interface Props {
  nodes: GraphNode[];
  edges: GraphEdge[];
  visibleBranches: Set<string>;
  highlightedNodeId: string | null;
  selectedNodeId: string | null;
  onNodeSelect: (id: string) => void;
  onNodeHover: (id: string | null) => void;
}

export function MindGraph({ nodes, edges, visibleBranches, highlightedNodeId, selectedNodeId, onNodeSelect, onNodeHover }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartInstanceRef = useRef<echarts.ECharts | null>(null);

  const filteredNodes = useMemo(
    () => nodes.filter((n) => visibleBranches.has(n.branch || "root")),
    [nodes, visibleBranches],
  );

  const filteredNodeIds = useMemo(() => new Set(filteredNodes.map((n) => n.id)), [filteredNodes]);

  const filteredEdges = useMemo(
    () => edges.filter((e) => filteredNodeIds.has(e.source) && filteredNodeIds.has(e.target)),
    [edges, filteredNodeIds],
  );

  const categories = useMemo(() => {
    const branches = [...new Set(filteredNodes.map((n) => n.branch || "root"))];
    return branches.map((b) => ({
      name: b,
      itemStyle: { color: getBranchColor(b) },
    }));
  }, [filteredNodes]);

  const categoryIndex = useMemo(() => {
    const map = new Map<string, number>();
    categories.forEach((c, i) => map.set(c.name, i));
    return map;
  }, [categories]);

  // Resolve theme color for labels
  const labelColor = useMemo(() => {
    const el = document.documentElement;
    return getComputedStyle(el).getPropertyValue("--color-base-content").trim() || "#1f2937";
  }, []);

  const option = useMemo(() => {
    const graphNodes = filteredNodes.map((n) => {
      const connections = n.linkCount + n.backlinkCount;
      const size = Math.max(8, Math.min(50, 10 + connections * 4));

      const isSelected = n.id === selectedNodeId;

      return {
        id: n.id,
        name: n.title || n.name,
        symbolSize: isSelected ? Math.max(size, 24) : size,
        category: categoryIndex.get(n.branch || "root") ?? 0,
        itemStyle: {
          color: getBranchColor(n.branch),
          borderColor: isSelected ? "#fff" : "transparent",
          borderWidth: isSelected ? 3 : 0,
          shadowBlur: isSelected ? 16 : 0,
          shadowColor: isSelected ? getBranchColor(n.branch) : "transparent",
        },
        label: {
          show: isSelected || size > LABEL_SIZE_THRESHOLD,
          fontWeight: isSelected ? ("bold" as const) : ("normal" as const),
        },
      };
    });

    const graphLinks = filteredEdges.map((e) => ({
      source: e.source,
      target: e.target,
    }));

    return {
      tooltip: {},
      legend: [
        {
          data: categories.map((c) => c.name),
          textStyle: { color: labelColor, fontSize: 11 },
          top: 12,
          left: 12,
        },
      ],
      animationDuration: 1500,
      animationEasingUpdate: "quinticInOut" as const,
      series: [
        {
          type: "graph",
          legendHoverLink: false,
          layout: "force",
          roam: true,
          draggable: true,
          data: graphNodes,
          links: graphLinks,
          categories,
          force: {
            repulsion: 200,
            edgeLength: [80, 160],
            gravity: 0.1,
            friction: 0.6,
          },
          label: {
            position: "right",
            formatter: (params: { name?: string }) => {
              const name = params.name || "";
              return name.length > 20 ? name.slice(0, 20) + "..." : name;
            },
            fontSize: 12,
            color: labelColor,
          },
          lineStyle: {
            color: "source",
            curveness: 0.3,
          },
          emphasis: {
            focus: "adjacency",
            lineStyle: {
              width: 10,
            },
          },
        },
      ],
    };
  }, [filteredNodes, filteredEdges, categories, categoryIndex, labelColor, selectedNodeId]);

  // Init chart
  useEffect(() => {
    if (!containerRef.current) return;

    const chart = echarts.init(containerRef.current);
    chartInstanceRef.current = chart;

    chart.on("click", (params) => {
      if (params.dataType === "node" && (params.data as { id?: string })?.id) {
        onNodeSelect((params.data as { id: string }).id);
      }
    });
    chart.on("mouseover", (params) => {
      if (params.dataType === "node" && (params.data as { id?: string })?.id) {
        onNodeHover((params.data as { id: string }).id);
      }
    });
    chart.on("mouseout", (params) => {
      if (params.dataType === "node") onNodeHover(null);
    });

    const observer = new ResizeObserver(() => chart.resize());
    observer.observe(containerRef.current);

    return () => {
      observer.disconnect();
      chart.dispose();
      chartInstanceRef.current = null;
    };
  }, [onNodeSelect, onNodeHover]);

  // Update options
  useEffect(() => {
    chartInstanceRef.current?.setOption(option, true);
  }, [option]);

  if (filteredNodes.length === 0) {
    return (
      <div className="h-full flex items-center justify-center text-base-content/60 text-sm">
        No vault files to display
      </div>
    );
  }

  return <div ref={containerRef} className="w-full h-full" />;
}
