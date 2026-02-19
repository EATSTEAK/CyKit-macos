import { useState, useCallback } from "react";
import { commands } from "../lib/protocol";

export function useRecording(sendCommand: (cmd: string) => void) {
  const [isRecording, setIsRecording] = useState(false);
  const [filename, setFilename] = useState("EEG-recording_1");

  const startRecording = useCallback(() => {
    sendCommand(commands.recordStart(filename));
    setIsRecording(true);
  }, [sendCommand, filename]);

  const stopRecording = useCallback(() => {
    sendCommand(commands.recordStop());
    setIsRecording(false);
  }, [sendCommand]);

  return {
    isRecording,
    filename,
    setFilename,
    startRecording,
    stopRecording,
  };
}
