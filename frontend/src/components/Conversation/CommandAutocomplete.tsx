import { type SlashCommandDef } from "../../constants/slashCommands";

interface Props {
  commands: SlashCommandDef[];
  selectedIndex: number;
  onSelect: (command: SlashCommandDef) => void;
}

export function CommandAutocomplete({ commands, selectedIndex, onSelect }: Props) {
  if (commands.length === 0) return null;

  return (
    <div className="absolute bottom-full left-0 right-0 mb-1">
      <ul className="menu bg-base-300 border border-neutral rounded-lg shadow-lg p-1 max-w-md">
        {commands.map((cmd, i) => (
          <li key={cmd.name}>
            <button
              className={`flex justify-between gap-4 text-sm py-1.5 ${
                i === selectedIndex ? "active" : ""
              }`}
              onMouseDown={(e) => {
                e.preventDefault();
                onSelect(cmd);
              }}
            >
              <span className="font-mono text-primary">
                /{cmd.name}
                {cmd.argHint && (
                  <span className="text-neutral-content ml-1">{cmd.argHint}</span>
                )}
              </span>
              <span className="text-neutral-content text-xs">{cmd.description}</span>
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}
