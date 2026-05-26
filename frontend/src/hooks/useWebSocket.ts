import { useEffect, useRef, useCallback } from "react";
import { WebSocketManager } from "@/api/websocket";

interface UseWebSocketOptions {
  url: string;
  onMessage?: (data: Record<string, unknown>) => void;
  onConnected?: () => void;
  onDisconnected?: () => void;
  autoConnect?: boolean;
}

export function useWebSocket({
  url,
  onMessage,
  onConnected,
  onDisconnected,
  autoConnect = true,
}: UseWebSocketOptions) {
  const managerRef = useRef<WebSocketManager | null>(null);

  useEffect(() => {
    const manager = new WebSocketManager(url);
    managerRef.current = manager;

    if (onMessage) {
      manager.on("message", onMessage);
    }
    if (onConnected) {
      manager.on("connected", onConnected);
    }
    if (onDisconnected) {
      manager.on("disconnected", onDisconnected);
    }

    if (autoConnect) {
      manager.connect();
    }

    return () => {
      manager.disconnect();
      managerRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [url]);

  const send = useCallback((data: Record<string, unknown>) => {
    managerRef.current?.send(data);
  }, []);

  const connect = useCallback(() => {
    managerRef.current?.connect();
  }, []);

  const disconnect = useCallback(() => {
    managerRef.current?.disconnect();
  }, []);

  return { send, connect, disconnect };
}
