/**
 * Parse an href and extract a vault document file path if it's an internal
 * document link. Returns the file path (e.g. "documents/unit-economics.md")
 * or null if the link is external / not a document link.
 *
 * Recognised patterns:
 *  - /agent/documents/filename.md  → documents/filename.md
 *  - /docs/:vaultId/path           → path (strips the route prefix)
 *  - Relative .md paths            → as-is
 */
export function parseVaultDocLink(href: string): string | null {
  // Normalise to a URL so we can inspect the pathname
  let pathname: string;
  try {
    const url = new URL(href, window.location.origin);
    // Only handle same-origin links
    if (url.origin !== window.location.origin) return null;
    pathname = url.pathname;
  } catch {
    // Relative path that failed URL parsing — treat as potential doc link
    pathname = href;
  }

  // Pattern: /agent/documents/...  (what agents currently generate)
  const agentDocMatch = pathname.match(/^\/agent\/documents\/(.+\.md)$/);
  if (agentDocMatch) return `documents/${agentDocMatch[1]}`;

  // Pattern: /docs/:vaultId/... (our canonical route)
  const docsRouteMatch = pathname.match(/^\/docs\/[^/]+\/(.+)$/);
  if (docsRouteMatch) return docsRouteMatch[1];

  // Pattern: bare relative .md path
  if (pathname.endsWith(".md") && !pathname.startsWith("http")) {
    return pathname.replace(/^\//, "");
  }

  return null;
}
