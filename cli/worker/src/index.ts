const SCRIPT_URL =
  "https://raw.githubusercontent.com/brandonkorous/axon/main/cli/install.sh";

export default {
  async fetch(request: Request): Promise<Response> {
    const url = new URL(request.url);

    // Health check
    if (url.pathname === "/health") {
      return new Response("ok");
    }

    // Fetch the install script from GitHub
    const script = await fetch(SCRIPT_URL, {
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
  },
};
