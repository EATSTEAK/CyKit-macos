import { useState, useCallback, useRef, useEffect } from "react";
import { commands } from "../lib/protocol";

export function useBaseline(sendCommand: (cmd: string) => void) {
  const [baselineEnabled, setBaselineEnabled] = useState(true);
  const [pyBaseline, setPyBaseline] = useState(true);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const toggleBaseline = useCallback(
    (enabled: boolean) => {
      setBaselineEnabled(enabled);
      const mode = pyBaseline && enabled ? 1 : 0;
      sendCommand(commands.setBaselineMode(mode));
    },
    [sendCommand, pyBaseline],
  );

  const togglePyBaseline = useCallback(
    (enabled: boolean) => {
      setPyBaseline(enabled);
      const mode = enabled && baselineEnabled ? 1 : 0;
      sendCommand(commands.setBaselineMode(mode));
    },
    [sendCommand, baselineEnabled],
  );

  const resetBaseline = useCallback(() => {
    toggleBaseline(false);
    setTimeout(() => toggleBaseline(true), 500);
  }, [toggleBaseline]);

  // Auto-reset baseline every 15 seconds (matching legacy behavior)
  useEffect(() => {
    intervalRef.current = setInterval(() => {
      if (baselineEnabled) {
        toggleBaseline(true);
      }
    }, 15000);

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [baselineEnabled, toggleBaseline]);

  return {
    baselineEnabled,
    pyBaseline,
    toggleBaseline,
    togglePyBaseline,
    resetBaseline,
  };
}
