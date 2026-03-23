import { useCallback, useEffect, useRef, useState } from "react";
import { orgWsPath } from "../stores/orgStore";

interface UseWebSocketOptions {
  url: string;
  onMessage: (data: Record<string, unknown>) => void;
  autoConnect?: boolean;
}

export function useWebSocket({ url, onMessage, autoConnect = true }: UseWebSocketOptions) {
  const wsRef = useRef<WebSocket | null>(null);
  const [connected, setConnected] = useState(false);
  const onMessageRef = useRef(onMessage);
  onMessageRef.current = onMessage;

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    // In dev, connect directly to backend to avoid Vite proxy WS issues
    const host = import.meta.env.DEV ? "127.0.0.1:8000" : window.location.host;
    // Use org-scoped path if multi-org is active
    const resolvedUrl = orgWsPath(url.replace(/^\/api\//, ""));
    const wsUrl = `${protocol}//${host}${resolvedUrl}`;
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => setConnected(true);
    ws.onclose = () => {
      setConnected(false);
      // Reconnect after 2 seconds
      setTimeout(connect, 2000);
    };
    ws.onerror = () => ws.close();
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        onMessageRef.current(data);
      } catch {
        // Ignore non-JSON messages (binary audio frames, etc.)
      }
    };

    wsRef.current = ws;
  }, [url]);

  const send = useCallback((data: Record<string, unknown>) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data));
    }
  }, []);

  const disconnect = useCallback(() => {
    wsRef.current?.close();
    wsRef.current = null;
  }, []);

  useEffect(() => {
    if (autoConnect) connect();
    return () => disconnect();
  }, [autoConnect, connect, disconnect]);

  return { connected, send, connect, disconnect };
}
