import { useState } from "react";
import type { ConnectionStatus } from "../../hooks/useWebSocket";

interface Props {
  status: ConnectionStatus;
  onConnect: (host: string, port: string) => void;
  onDisconnect: () => void;
}

export function ConnectionPanel({ status, onConnect, onDisconnect }: Props) {
  const [host, setHost] = useState("127.0.0.1");
  const [port, setPort] = useState("54123");

  const isConnected = status === "connected";
  const isConnecting = status === "connecting";

  return (
    <div className="flex items-center gap-2">
      <label className="text-text-dim text-[10px]">HOST</label>
      <input
        type="text"
        value={host}
        onChange={(e) => setHost(e.target.value)}
        disabled={isConnected}
        className="w-28"
      />
      <label className="text-text-dim text-[10px]">PORT</label>
      <input
        type="text"
        value={port}
        onChange={(e) => setPort(e.target.value)}
        maxLength={5}
        disabled={isConnected}
        className="w-16"
      />
      {!isConnected ? (
        <button
          onClick={() => onConnect(host, port)}
          disabled={isConnecting}
          className="border-accent text-accent hover:bg-accent hover:text-bg"
        >
          {isConnecting ? "Connecting..." : "Connect"}
        </button>
      ) : (
        <button
          onClick={onDisconnect}
          className="border-red text-red hover:bg-red hover:text-bg"
        >
          Disconnect
        </button>
      )}
      <StatusIndicator status={status} />
    </div>
  );
}

function StatusIndicator({ status }: { status: ConnectionStatus }) {
  const color =
    status === "connected"
      ? "bg-accent"
      : status === "connecting"
        ? "bg-orange"
        : "bg-border-light";

  return (
    <div className="flex items-center gap-1.5 ml-2">
      <div className={`w-2 h-2 ${color} ${status === "connecting" ? "animate-pulse" : ""}`} />
      <span className="text-[10px] text-text-dim uppercase tracking-wider">
        {status}
      </span>
    </div>
  );
}
