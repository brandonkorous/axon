import { useCallback, useEffect, useRef } from "react";

interface ResizeHandleProps {
  direction: "horizontal" | "vertical";
  onResize: (delta: number) => void;
  onResizeEnd?: () => void;
  className?: string;
}

export function ResizeHandle({ direction, onResize, onResizeEnd, className = "" }: ResizeHandleProps) {
  const dragging = useRef(false);
  const lastPos = useRef(0);

  const handleMouseDown = useCallback(
    (e: React.MouseEvent) => {
      e.preventDefault();
      dragging.current = true;
      lastPos.current = direction === "horizontal" ? e.clientX : e.clientY;
      document.body.style.cursor = direction === "horizontal" ? "col-resize" : "row-resize";
      document.body.style.userSelect = "none";
    },
    [direction],
  );

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!dragging.current) return;
      const pos = direction === "horizontal" ? e.clientX : e.clientY;
      const delta = pos - lastPos.current;
      lastPos.current = pos;
      onResize(delta);
    };

    const handleMouseUp = () => {
      if (!dragging.current) return;
      dragging.current = false;
      document.body.style.cursor = "";
      document.body.style.userSelect = "";
      onResizeEnd?.();
    };

    window.addEventListener("mousemove", handleMouseMove);
    window.addEventListener("mouseup", handleMouseUp);
    return () => {
      window.removeEventListener("mousemove", handleMouseMove);
      window.removeEventListener("mouseup", handleMouseUp);
    };
  }, [direction, onResize, onResizeEnd]);

  const isHorizontal = direction === "horizontal";

  return (
    <div
      onMouseDown={handleMouseDown}
      className={`
        ${isHorizontal ? "w-1 cursor-col-resize" : "h-1 cursor-row-resize"}
        flex-shrink-0 bg-transparent hover:bg-primary/30 active:bg-primary/50
        transition-colors duration-150 z-10
        ${className}
      `}
      role="separator"
      aria-orientation={isHorizontal ? "vertical" : "horizontal"}
    />
  );
}
