import { useState, useCallback } from "react";
import { useTabStore, type SplitDirection } from "../../stores/tabStore";

interface DropZoneProps {
    groupId: string;
}

type DropPosition = "left" | "right" | "top" | "bottom" | "center" | null;

export function DropZone({ groupId }: DropZoneProps) {
    const [position, setPosition] = useState<DropPosition>(null);
    const [isDragging, setIsDragging] = useState(false);
    const splitGroup = useTabStore((s) => s.splitGroup);
    const moveTab = useTabStore((s) => s.moveTab);
    const tabDragging = useTabStore((s) => s.tabDragging);

    const handleDragOver = useCallback((e: React.DragEvent) => {
        if (!e.dataTransfer.types.includes("text/axon-tab")) return;
        e.preventDefault();
        e.dataTransfer.dropEffect = "move";
        setIsDragging(true);

        const rect = e.currentTarget.getBoundingClientRect();
        const x = (e.clientX - rect.left) / rect.width;
        const y = (e.clientY - rect.top) / rect.height;

        // Determine drop position based on cursor location
        const edgeThreshold = 0.25;
        if (x < edgeThreshold) setPosition("left");
        else if (x > 1 - edgeThreshold) setPosition("right");
        else if (y < edgeThreshold) setPosition("top");
        else if (y > 1 - edgeThreshold) setPosition("bottom");
        else setPosition("center");
    }, []);

    const handleDragLeave = useCallback(() => {
        setIsDragging(false);
        setPosition(null);
    }, []);

    const handleDrop = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(false);
        setPosition(null);

        const tabId = e.dataTransfer.getData("text/axon-tab");
        if (!tabId || !position) return;

        if (position === "center") {
            // Move tab to this group
            const group = useTabStore.getState().groups[groupId];
            moveTab(tabId, group?.tabs.length || 0, groupId);
        } else {
            // Split the group
            const direction: SplitDirection =
                position === "left" || position === "right" ? "horizontal" : "vertical";
            splitGroup(groupId, direction, tabId);
        }
    }, [position, groupId, splitGroup, moveTab]);

    // Only render the drop overlay when a tab is actively being dragged
    if (!tabDragging) return null;

    return (
        <div
            className="absolute inset-0 z-20"
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
        >
            {isDragging && (
                <>
                    {position === "left" && (
                        <div className="absolute inset-y-0 left-0 w-1/2 bg-primary/10 border-2 border-primary/30 rounded-l pointer-events-none" />
                    )}
                    {position === "right" && (
                        <div className="absolute inset-y-0 right-0 w-1/2 bg-primary/10 border-2 border-primary/30 rounded-r pointer-events-none" />
                    )}
                    {position === "top" && (
                        <div className="absolute inset-x-0 top-0 h-1/2 bg-primary/10 border-2 border-primary/30 rounded-t pointer-events-none" />
                    )}
                    {position === "bottom" && (
                        <div className="absolute inset-x-0 bottom-0 h-1/2 bg-primary/10 border-2 border-primary/30 rounded-b pointer-events-none" />
                    )}
                    {position === "center" && (
                        <div className="absolute inset-0 bg-primary/10 border-2 border-primary/30 rounded pointer-events-none" />
                    )}
                </>
            )}
        </div>
    );
}
