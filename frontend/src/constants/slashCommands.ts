export interface SlashCommandDef {
  name: string;
  description: string;
  hasArgs: boolean;
  argHint?: string;
}

export const SLASH_COMMANDS: SlashCommandDef[] = [
  { name: "sleep", description: "Trigger memory consolidation", hasArgs: false },
  { name: "remember", description: "Force-write a vault entry", hasArgs: true, argHint: "<text>" },
  { name: "forget", description: "Archive matching vault entries", hasArgs: true, argHint: "<query>" },
  { name: "recall", description: "Search memory and surface results", hasArgs: true, argHint: "<query>" },
  { name: "tasks", description: "Show running/pending tasks", hasArgs: false },
  { name: "status", description: "Agent status, memory stats", hasArgs: false },
  { name: "discover", description: "Search available capabilities", hasArgs: true, argHint: "<query>" },
];
