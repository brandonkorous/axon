import { useEffect, useMemo, useRef, useState } from "react";
import * as echarts from "echarts/core";
import { TreeChart } from "echarts/charts";
import { TooltipComponent } from "echarts/components";
import { CanvasRenderer } from "echarts/renderers";
import { orgApiPath } from "../../stores/orgStore";

echarts.use([TreeChart, TooltipComponent, CanvasRenderer]);

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

const STATUS_COLORS: Record<string, string> = {
  active: "#22c55e",
  paused: "#f59e0b",
  disabled: "#9ca3af",
  terminated: "#ef4444",
};

interface ThemeColors {
  label: string;
  cardBg: string;
  cardBorder: string;
}

interface TreeNode {
  name: string;
  value: string;
  symbol: string;
  symbolSize: number;
  itemStyle: { color: string; borderColor: string; borderWidth: number };
  label: Record<string, unknown>;
  children: TreeNode[];
}

function buildTreeData(chartData: ChartData, theme: ThemeColors): TreeNode[] {
  // Group children by parent
  const childrenOf = new Map<string, ChartNode[]>();
  for (const n of chartData.nodes) {
    if (n.parent_id) {
      const list = childrenOf.get(n.parent_id) || [];
      list.push(n);
      childrenOf.set(n.parent_id, list);
    }
  }

  function toTreeNode(node: ChartNode): TreeNode {
    const children = childrenOf.get(node.id) || [];
    const statusColor = STATUS_COLORS[node.status] || STATUS_COLORS.active;
    const initial = node.name[0]?.toUpperCase() || "?";

    return {
      name: node.name,
      value: node.id,
      symbol: "circle",
      symbolSize: 0,
      itemStyle: {
        color: node.color,
        borderColor: statusColor,
        borderWidth: 3,
      },
      label: {
        show: true,
        formatter: [
          `{avatar|${initial}}`,
          "{gap| }",
          `{name|${node.name}}`,
          `{title|${node.title}}`,
          node.has_strategy_override ? "{override|strategy override}" : "",
        ].filter(Boolean).join("\n"),
        backgroundColor: theme.cardBg,
        borderColor: theme.cardBorder,
        borderWidth: 1,
        borderRadius: 8,
        padding: [12, 16, 12, 16],
        align: "center",
        rich: {
          avatar: {
            width: 36,
            height: 36,
            borderRadius: 18,
            backgroundColor: node.color,
            color: "#fff",
            fontSize: 14,
            fontWeight: "bold" as const,
            align: "center",
            lineHeight: 36,
            padding: [0, 0, 0, 0],
            shadowBlur: 4,
            shadowOffsetY: 1,
            shadowColor: `${statusColor}88`,
          },
          gap: {
            fontSize: 1,
            lineHeight: 8,
          },
          name: {
            fontSize: 13,
            fontWeight: "bold" as const,
            color: theme.label,
            lineHeight: 20,
          },
          title: {
            fontSize: 10,
            color: theme.label + "99",
            lineHeight: 16,
          },
          override: {
            fontSize: 9,
            color: "#84cc16",
            lineHeight: 16,
            padding: [2, 0, 0, 0],
          },
        },
      },
      children: children.map(toTreeNode),
    };
  }

  // Find root nodes (no parent_id)
  const roots = chartData.nodes.filter((n) => !n.parent_id);

  // If there's an "axon" node, make it the single root
  const axon = roots.find((n) => n.id === "axon");
  if (axon) {
    const otherRoots = roots.filter((n) => n.id !== "axon");
    const axonTree = toTreeNode(axon);
    for (const r of otherRoots) {
      if (!axonTree.children.some((c) => c.value === r.id)) {
        axonTree.children.push(toTreeNode(r));
      }
    }
    return [axonTree];
  }

  return roots.map(toTreeNode);
}

export function OrgChartView() {
  const [chartData, setChartData] = useState<ChartData | null>(null);
  const [loading, setLoading] = useState(true);
  const containerRef = useRef<HTMLDivElement>(null);
  const chartInstanceRef = useRef<echarts.ECharts | null>(null);

  const theme = useMemo((): ThemeColors => {
    const s = getComputedStyle(document.documentElement);
    const get = (v: string, fallback: string) => s.getPropertyValue(v).trim() || fallback;
    return {
      label: get("--color-base-content", "#1f2937"),
      cardBg: get("--color-base-300", "#d5c4a1"),
      cardBorder: get("--color-secondary", "#c9a87c"),
    };
  }, []);

  useEffect(() => {
    fetch(orgApiPath("org-chart"))
      .then((r) => r.json())
      .then((data) => {
        setChartData(data);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  const option = useMemo(() => {
    if (!chartData) return null;

    const treeData = buildTreeData(chartData, theme);

    return {
      tooltip: {
        trigger: "item" as const,
        formatter: (params: { data?: { name?: string } }) => params.data?.name || "",
      },
      series: [
        {
          type: "tree",
          data: treeData,
          top: 60,
          bottom: 60,
          left: 80,
          right: 80,
          layout: "orthogonal",
          orient: "TB",
          symbol: "none",
          symbolSize: 0,
          edgeShape: "polyline",
          edgeForkPosition: "50%",
          initialTreeDepth: -1,
          roam: true,
          label: {
            position: "inside",
            verticalAlign: "middle",
            align: "center",
          },
          lineStyle: {
            color: theme.cardBorder,
            width: 2,
            curveness: 0,
          },
          emphasis: {
            focus: "ancestor",
            label: {
              shadowBlur: 8,
              shadowColor: "rgba(0,0,0,0.15)",
            },
          },
          expandAndCollapse: false,
          animationDuration: 600,
          animationEasingUpdate: "quinticInOut" as const,
        },
      ],
    };
  }, [chartData, theme]);

  useEffect(() => {
    const el = containerRef.current;
    if (!el || !option) return;

    const chart = chartInstanceRef.current ?? echarts.init(el);
    chartInstanceRef.current = chart;
    chart.setOption(option, true);

    const observer = new ResizeObserver(() => chart.resize());
    observer.observe(el);

    return () => {
      observer.disconnect();
      chart.dispose();
      chartInstanceRef.current = null;
    };
  }, [option]);

  return (
    <div className="h-full flex flex-col">
      <div className="px-4 sm:px-6 py-3 sm:py-4 border-b border-neutral">
        <h1 className="text-lg sm:text-xl font-bold text-base-content">Org Chart</h1>
        <p className="text-xs text-base-content/60">
          Agent hierarchy and delegation relationships
        </p>
      </div>
      <div className="flex-1 min-h-0 relative" ref={containerRef}>
        {loading && (
          <div className="absolute inset-0 flex items-center justify-center">
            <span className="loading loading-spinner loading-md text-primary" />
          </div>
        )}
      </div>
    </div>
  );
}
