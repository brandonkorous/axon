import { Suspense, useCallback, useRef } from "react";
import { useTabStore, type SplitNode } from "../../stores/tabStore";
import { TabBar } from "./TabBar";
import { TabContent } from "./TabContent";
import { DropZone } from "./DropZone";
import { ResizeHandle } from "./ResizeHandle";

export function SplitContainer() {
  const splitRoot = useTabStore((s) => s.splitRoot);
  return (
    <div className="flex-1 overflow-hidden">
      <SplitNodeRenderer node={splitRoot} path={[]} />
    </div>
  );
}

function SplitNodeRenderer({ node, path }: { node: SplitNode; path: number[] }) {
  if (node.type === "leaf") {
    return <LeafGroup groupId={node.groupId} />;
  }

  return (
    <BranchRenderer
      direction={node.direction}
      children={node.children}
      sizes={node.sizes}
      path={path}
    />
  );
}

function BranchRenderer({
  direction,
  children,
  sizes,
  path,
}: {
  direction: "horizontal" | "vertical";
  children: SplitNode[];
  sizes: number[];
  path: number[];
}) {
  const resizeSplit = useTabStore((s) => s.resizeSplit);
  const sizesRef = useRef(sizes);
  sizesRef.current = sizes;

  const handleResize = useCallback(
    (index: number, delta: number, containerSize: number) => {
      const currentSizes = [...sizesRef.current];
      const deltaPct = (delta / containerSize) * 100;
      const minPct = 10; // minimum 10% per pane

      let newA = currentSizes[index] + deltaPct;
      let newB = currentSizes[index + 1] - deltaPct;

      if (newA < minPct) { newA = minPct; newB = currentSizes[index] + currentSizes[index + 1] - minPct; }
      if (newB < minPct) { newB = minPct; newA = currentSizes[index] + currentSizes[index + 1] - minPct; }

      currentSizes[index] = newA;
      currentSizes[index + 1] = newB;
      resizeSplit(path, currentSizes);
    },
    [resizeSplit, path],
  );

  const isHorizontal = direction === "horizontal";

  return (
    <div className={`flex ${isHorizontal ? "flex-row" : "flex-col"} h-full w-full overflow-hidden`}>
      {children.map((child, i) => (
        <SplitPane key={i} index={i} total={children.length} direction={direction} size={sizes[i]} onResize={handleResize}>
          <SplitNodeRenderer node={child} path={[...path, i]} />
        </SplitPane>
      ))}
    </div>
  );
}

function SplitPane({
  index,
  total,
  direction,
  size,
  onResize,
  children,
}: {
  index: number;
  total: number;
  direction: "horizontal" | "vertical";
  size: number;
  onResize: (index: number, delta: number, containerSize: number) => void;
  children: React.ReactNode;
}) {
  const containerRef = useRef<HTMLDivElement>(null);
  const isHorizontal = direction === "horizontal";
  const showHandle = index < total - 1;

  const handleResizeDelta = useCallback(
    (delta: number) => {
      if (!containerRef.current) return;
      const parent = containerRef.current.parentElement;
      if (!parent) return;
      const containerSize = isHorizontal ? parent.offsetWidth : parent.offsetHeight;
      onResize(index, delta, containerSize);
    },
    [index, onResize, isHorizontal],
  );

  return (
    <>
      <div
        ref={containerRef}
        className="overflow-hidden min-w-0 min-h-0"
        style={{
          [isHorizontal ? "width" : "height"]: `${size}%`,
          flexShrink: 0,
          flexGrow: 0,
        }}
      >
        {children}
      </div>
      {showHandle && (
        <ResizeHandle
          direction={isHorizontal ? "horizontal" : "vertical"}
          onResize={handleResizeDelta}
        />
      )}
    </>
  );
}

function LeafGroup({ groupId }: { groupId: string }) {
  const hasTabs = useTabStore((s) => (s.groups[groupId]?.tabs.length ?? 0) > 0);
  const isActiveGroup = useTabStore((s) => s.activeGroupId === groupId);

  return (
    <div
      className={`flex flex-col h-full relative ${
        isActiveGroup ? "" : "opacity-90"
      }`}
      onClick={() => {
        if (groupId !== useTabStore.getState().activeGroupId) {
          useTabStore.setState({ activeGroupId: groupId });
        }
      }}
    >
      {hasTabs && <TabBar groupId={groupId} />}
      <div className="flex-1 overflow-hidden relative">
        <TabContent groupId={groupId} />
        <DropZone groupId={groupId} />
      </div>
    </div>
  );
}
