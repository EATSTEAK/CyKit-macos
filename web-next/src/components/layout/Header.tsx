import { ConnectionPanel } from "../connection/ConnectionPanel";
import type { ConnectionStatus } from "../../hooks/useWebSocket";

interface Props {
  status: ConnectionStatus;
  onConnect: (host: string, port: string) => void;
  onDisconnect: () => void;
}

export function Header({ status, onConnect, onDisconnect }: Props) {
  return (
    <header className="h-11 border-b border-border bg-panel flex items-center px-4 gap-4 shrink-0">
      <div className="flex items-center gap-2 mr-4">
        <span className="text-accent font-bold text-sm tracking-wider">CyKIT</span>
        <span className="text-text-muted text-[10px]">v2</span>
      </div>
      <div className="h-4 border-l border-border" />
      <ConnectionPanel
        status={status}
        onConnect={onConnect}
        onDisconnect={onDisconnect}
      />
    </header>
  );
}
