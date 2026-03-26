export interface AutocompleteItem {
  key: string;
  label: string;
  detail?: string;
  hint?: string;
  color?: string;
}

interface Props {
  items: AutocompleteItem[];
  selectedIndex: number;
  onSelect: (item: AutocompleteItem) => void;
}

export function InputAutocomplete({ items, selectedIndex, onSelect }: Props) {
  if (items.length === 0) return null;

  return (
    <div className="absolute bottom-full left-0 right-0 mb-1">
      <ul className="menu bg-base-300 border border-neutral rounded-lg shadow-lg p-1 max-w-md">
        {items.map((item, i) => (
          <li key={item.key}>
            <button
              className={`flex items-center gap-3 text-sm py-1.5 ${
                i === selectedIndex ? "active" : ""
              }`}
              onMouseDown={(e) => {
                e.preventDefault();
                onSelect(item);
              }}
            >
              {item.color && (
                <span
                  className="w-5 h-5 rounded-full shrink-0 flex items-center justify-center text-[10px] font-bold text-white"
                  style={{ backgroundColor: item.color }}
                >
                  {item.label.replace(/^[@/]/, "")[0]?.toUpperCase()}
                </span>
              )}
              <span className="font-mono text-primary">
                {item.label}
                {item.hint && (
                  <span className="text-base-content/60 ml-1">{item.hint}</span>
                )}
              </span>
              {item.detail && (
                <span className="text-base-content/60 text-xs ml-auto">{item.detail}</span>
              )}
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}
