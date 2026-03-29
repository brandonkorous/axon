import { useId, type ReactNode } from "react";

interface StatusBarPopoverProps {
    /** Trigger button content */
    trigger: ReactNode;
    /** Popover panel content */
    children: ReactNode;
    /** aria-label for the trigger */
    label: string;
    /** Panel width class, e.g. "w-80" */
    width?: string;
}

export function StatusBarPopover({
    trigger,
    children,
    label,
    width = "w-80",
}: StatusBarPopoverProps) {
    const id = useId();
    const popoverId = `sb-popover-${id}`;
    const anchorName = `--sb-anchor-${id}`;

    return (
        <>
            <button
                className="px-2 h-full flex items-center gap-1.5 hover:bg-base-content/10 transition-colors text-base-content/70 hover:text-base-content focus-visible:outline focus-visible:outline-primary cursor-pointer"
                aria-label={label}
                popoverTarget={popoverId}
                style={{ anchorName } as React.CSSProperties}
            >
                {trigger}
            </button>
            <div
                className={`dropdown ${width} mb-8 max-h-80 bg-base-200 border border-base-content/10 rounded-lg shadow-lg`}
                popover="auto"
                id={popoverId}
                style={{ positionAnchor: anchorName } as React.CSSProperties}
            >
                <div className="flex flex-col">
                    {children}
                </div>
            </div>
        </>
    );
}
