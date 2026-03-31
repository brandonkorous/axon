const SHELL_SCRIPT_URL =
  "https://raw.githubusercontent.com/brandonkorous/axon/main/cli/install.sh";
const POWERSHELL_SCRIPT_URL =
  "https://raw.githubusercontent.com/brandonkorous/axon/main/cli/install.ps1";

function isPowerShell(request: Request): boolean {
  const ua = request.headers.get("user-agent") || "";
  // PowerShell's Invoke-RestMethod / Invoke-WebRequest sends a distinctive UA
  return /WindowsPowerShell|PowerShell|PSVersion/i.test(ua);
}

export default {
  async fetch(request: Request): Promise<Response> {
    const url = new URL(request.url);

    if (url.pathname === "/health") {
      return new Response("ok");
    }

    // Explicit platform endpoints
    if (url.pathname === "/win" || url.pathname === "/windows") {
      return fetchScript(POWERSHELL_SCRIPT_URL);
    }
    if (url.pathname === "/sh" || url.pathname === "/unix") {
      return fetchScript(SHELL_SCRIPT_URL);
    }

    // Auto-detect: PowerShell UA → PowerShell script, otherwise shell script
    const scriptUrl = isPowerShell(request)
      ? POWERSHELL_SCRIPT_URL
      : SHELL_SCRIPT_URL;

    return fetchScript(scriptUrl);
  },
};

async function fetchScript(scriptUrl: string): Promise<Response> {
  const script = await fetch(scriptUrl, {
    cf: { cacheTtl: 300, cacheEverything: true },
  });

  if (!script.ok) {
    return new Response("Failed to fetch install script", { status: 502 });
  }

  const body = await script.text();

  return new Response(body, {
    headers: {
      "content-type": "text/plain; charset=utf-8",
      "cache-control": "public, max-age=300",
      "x-axon-source": "cloudflare-worker",
    },
  });
}
