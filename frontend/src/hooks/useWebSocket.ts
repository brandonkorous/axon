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
  // Flag to prevent zombie reconnects after intentional disconnect
  const intentionalCloseRef = useRef(false);
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    // Clean up any existing connection before creating a new one
    if (wsRef.current) {
      wsRef.current.onclose = null;
      wsRef.current.onerror = null;
      wsRef.current.onmessage = null;
      wsRef.current.onopen = null;
      if (wsRef.current.readyState !== WebSocket.CLOSED) {
        wsRef.current.close();
      }
      wsRef.current = null;
    }

    intentionalCloseRef.current = false;

    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    // In dev, connect directly to backend to avoid Vite proxy WS issues
    const host = import.meta.env.DEV ? "127.0.0.1:8000" : window.location.host;
    // Use org-scoped path if multi-org is active
    const resolvedUrl = orgWsPath(url.replace(/^\/api\//, ""));
    const wsUrl = `${protocol}//${host}${resolvedUrl}`;
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => setConnected(true);
    ws.onclose = (event) => {
      setConnected(false);
      // Don't reconnect on intentional close or permanent errors (4004 = not found)
      if (intentionalCloseRef.current || event.code === 4004) {
        return;
      }
      reconnectTimerRef.current = setTimeout(connect, 2000);
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
    intentionalCloseRef.current = true;
    if (reconnectTimerRef.current) {
      clearTimeout(reconnectTimerRef.current);
      reconnectTimerRef.current = null;
    }
    if (wsRef.current) {
      wsRef.current.onclose = null;
      wsRef.current.close();
      wsRef.current = null;
    }
    setConnected(false);
  }, []);

  useEffect(() => {
    if (autoConnect) connect();
    return () => disconnect();
  }, [autoConnect, connect, disconnect]);

  return { connected, send, connect, disconnect };
}
