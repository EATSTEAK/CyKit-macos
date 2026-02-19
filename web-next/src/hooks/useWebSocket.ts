import { useRef, useState, useCallback } from "react";
import {
  SPLIT_TOKEN,
  parseRawMessage,
  classifyPayload,
  parseInfoCommand,
  commands,
  type CommandMessage,
  type DataMessage,
} from "../lib/protocol";

export type ConnectionStatus = "disconnected" | "connecting" | "connected";

export interface WebSocketCallbacks {
  onCommand?: (msg: CommandMessage) => void;
  onData?: (msg: DataMessage) => void;
  onStatusChange?: (status: ConnectionStatus) => void;
}

export function useWebSocket(callbacks: WebSocketCallbacks) {
  const [status, setStatus] = useState<ConnectionStatus>("disconnected");
  const socketRef = useRef<WebSocket | null>(null);
  const uidRef = useRef("");
  const signRef = useRef("");

  const updateStatus = useCallback(
    (s: ConnectionStatus) => {
      setStatus(s);
      callbacks.onStatusChange?.(s);
    },
    [callbacks],
  );

  const connect = useCallback(
    (host: string, port: string) => {
      if (
        socketRef.current &&
        socketRef.current.readyState !== WebSocket.CLOSED
      ) {
        return;
      }

      updateStatus("connecting");

      const ws = new WebSocket(`ws://${host}:${port}/CyKITv2`);
      socketRef.current = ws;

      ws.onopen = () => {
        console.log("[CyKIT] Socket Open");
      };

      ws.onmessage = (event: MessageEvent) => {
        const { uid, sign, payload } = parseRawMessage(event.data);
        uidRef.current = uid;
        signRef.current = sign;

        const classified = classifyPayload(payload);

        switch (classified.type) {
          case "registration":
            updateStatus("connected");
            break;
          case "command": {
            callbacks.onCommand?.(classified);
            break;
          }
          case "data":
            callbacks.onData?.(classified);
            break;
        }
      };

      ws.onclose = () => {
        updateStatus("disconnected");
        socketRef.current = null;
      };

      ws.onerror = () => {
        updateStatus("disconnected");
      };
    },
    [callbacks, updateStatus],
  );

  const disconnect = useCallback(() => {
    if (!socketRef.current) return;
    sendCommand(commands.disconnect());
    socketRef.current.close();
    socketRef.current = null;
    updateStatus("disconnected");
  }, [updateStatus]);

  const sendCommand = useCallback((text: string) => {
    const ws = socketRef.current;
    if (!ws || ws.readyState !== WebSocket.OPEN) return;
    const data = `${uidRef.current}${SPLIT_TOKEN}${signRef.current}${SPLIT_TOKEN}${text}`;
    ws.send(data);
  }, []);

  return {
    status,
    connect,
    disconnect,
    sendCommand,
  };
}

export { parseInfoCommand, commands };
