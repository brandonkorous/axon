/** Format a cost value for display — always shows the real value, no matter how small. */
export function formatCost(cost: number): string {
  if (cost === 0) return "$0.00";
  // Find enough decimal places to show at least 2 significant digits
  const decimals = Math.max(2, -Math.floor(Math.log10(cost)) + 1);
  return `$${cost.toFixed(decimals)}`;
}

/** Format a token count with k/M suffixes. */
export function formatTokens(tokens: number): string {
  if (tokens >= 1_000_000) return `${(tokens / 1_000_000).toFixed(1)}M`;
  if (tokens >= 1_000) return `${(tokens / 1_000).toFixed(1)}k`;
  return String(tokens);
}
