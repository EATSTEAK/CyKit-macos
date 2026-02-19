/**
 * CyKITv2 WebSocket Protocol
 *
 * Message format: uid<split>sign<split>payload
 * Command prefix: "CyKITv2:::"
 */

export const SPLIT_TOKEN = "<split>";
export const CMD_PREFIX = "CyKITv2:::";

// --- Command builders ---

export function buildCommand(command: string, ...args: (string | number)[]): string {
  let msg = `${CMD_PREFIX}${command}`;
  for (const arg of args) {
    msg += `:::${arg}`;
  }
  return msg;
}

export const commands = {
  disconnect: () => buildCommand("Disconnect"),
  setDataMode: (mode: number) => buildCommand("setDataMode", mode),
  setModel: (modelId: number) => buildCommand("setModel", modelId),
  changeFormat: (format: number) => buildCommand("changeFormat", format),
  setBaselineMode: (mode: number) => buildCommand("setBaselineMode", mode),
  updateSettings: (mode: number) => buildCommand("UpdateSettings", mode),
  setMask: (mask: string, newMask: string) => buildCommand("setMask", mask, newMask),
  recordStart: (filename: string) => buildCommand("RecordStart", filename),
  recordStop: () => buildCommand("RecordStop"),
} as const;

// --- Response parsing ---

export interface ParsedMessage {
  uid: string;
  sign: string;
  payload: string;
}

export function parseRawMessage(raw: string): ParsedMessage {
  const parts = raw.split(SPLIT_TOKEN);
  return {
    uid: parts[0] ?? "",
    sign: parts[1] ?? "",
    payload: parts[2] ?? "",
  };
}

export type CommandMessage = {
  type: "command";
  parts: string[]; // e.g. ["CyKITv2", "Info", "device", "EPOC+"]
};

export type DataMessage = {
  type: "data";
  raw: string;
};

export type RegistrationMessage = {
  type: "registration";
};

export function classifyPayload(
  payload: string,
): CommandMessage | DataMessage | RegistrationMessage {
  if (payload === "SETUID") {
    return { type: "registration" };
  }

  if (payload.startsWith(CMD_PREFIX)) {
    const parts = payload.split(":::");
    return { type: "command", parts };
  }

  return { type: "data", raw: payload };
}

// --- Device info parsing from commands ---

export interface DeviceInfoUpdate {
  field: "status" | "device" | "serial" | "keymodel" | "config" | "delimiter" | "baseline" | "datamode";
  value: string;
}

export function parseInfoCommand(parts: string[]): DeviceInfoUpdate | null {
  // parts[0] = "CyKITv2"
  const cmd = parts[1];

  if (cmd === "Connected") {
    return { field: "status", value: "Connected" };
  }

  if (cmd === "Info") {
    const subCmd = parts[2];
    if (subCmd === "device" || subCmd === "serial" || subCmd === "keymodel" || subCmd === "config" || subCmd === "delimiter") {
      return { field: subCmd, value: parts[3] ?? "" };
    }
  }

  if (cmd === "Baseline") {
    return { field: "baseline", value: parts[2] ?? "" };
  }

  if (cmd === "datamode") {
    return { field: "datamode", value: parts[2] ?? "" };
  }

  return null;
}
