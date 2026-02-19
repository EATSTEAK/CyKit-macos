import { useState, useCallback, useRef } from "react";
import type { CommandMessage } from "../lib/protocol";
import { parseInfoCommand } from "../lib/protocol";
import type { DeviceModelConfig, ParseOptions } from "../lib/models/types";
import { getModelConfig, MODEL_TYPES } from "../lib/models/registry";

export interface DeviceInfo {
  status: string;
  device: string;
  serial: string;
  keyModel: number;
  keyModelDisplay: string;
  headset: string;
  battery: string;
  config: ConfigFlags;
  delimiter: string;
}

export interface ConfigFlags {
  noCounter: boolean;
  noBattery: boolean;
  bluetooth: boolean;
  outputData: boolean;
  filter: boolean;
  dataMode: number;
}

const defaultDeviceInfo: DeviceInfo = {
  status: "Not Connected",
  device: "N/A",
  serial: "N/A",
  keyModel: 0,
  keyModelDisplay: "N/A",
  headset: "None",
  battery: "N/A",
  config: {
    noCounter: false,
    noBattery: false,
    bluetooth: false,
    outputData: false,
    filter: false,
    dataMode: 1,
  },
  delimiter: ",",
};

export function useDeviceInfo() {
  const [info, setInfo] = useState<DeviceInfo>(defaultDeviceInfo);
  const modelConfigRef = useRef<DeviceModelConfig | null>(null);
  const parseOptsRef = useRef<ParseOptions>({
    formatType: 0,
    noCounter: false,
    noBattery: false,
    bluetooth: false,
    outputData: false,
    delimiter: ",",
  });

  const handleCommand = useCallback((msg: CommandMessage) => {
    const update = parseInfoCommand(msg.parts);
    if (!update) return;

    setInfo((prev) => {
      const next = { ...prev };

      switch (update.field) {
        case "status":
          next.status = update.value;
          break;
        case "device":
          next.device = update.value;
          break;
        case "serial":
          next.serial = update.value;
          break;
        case "keymodel": {
          const keyId = parseInt(update.value, 10);
          next.keyModel = keyId;
          next.keyModelDisplay = update.value;
          next.headset = MODEL_TYPES[keyId] ?? "Unknown";

          const cfg = getModelConfig(keyId);
          modelConfigRef.current = cfg;
          break;
        }
        case "config": {
          const flags = update.value;
          const hasOutputData = flags.includes("outputdata");
          const config: ConfigFlags = {
            noCounter: flags.includes("nocounter"),
            noBattery: flags.includes("nobattery"),
            bluetooth: flags.includes("bluetooth"),
            outputData: hasOutputData,
            filter: flags.includes("filter"),
            dataMode: flags.includes("gyromode") ? 2 : 1,
          };
          next.config = config;

          // Update parse options
          // When outputdata is present Python pre-converts to float,
          // so formatType stays 0 even for bluetooth.
          parseOptsRef.current = {
            ...parseOptsRef.current,
            noCounter: config.noCounter,
            noBattery: config.noBattery,
            bluetooth: config.bluetooth,
            outputData: hasOutputData,
            formatType: (config.bluetooth && !hasOutputData) ? 1 : 0,
          };

          if (config.noBattery || config.noCounter) {
            next.battery = "N/A";
          }
          break;
        }
        case "delimiter": {
          const charCode = parseInt(update.value, 10);
          if (!isNaN(charCode)) {
            const delim = String.fromCharCode(charCode);
            next.delimiter = delim;
            parseOptsRef.current.delimiter = delim;
          }
          break;
        }
        case "datamode":
          next.config = { ...next.config, dataMode: parseInt(update.value, 10) };
          break;
      }

      return next;
    });
  }, []);

  const setFormatType = useCallback((localFormat: number) => {
    parseOptsRef.current = {
      ...parseOptsRef.current,
      formatType: localFormat,
    };
  }, []);

  const updateBattery = useCallback((percent: number) => {
    setInfo((prev) => ({
      ...prev,
      battery: `${Math.round(percent)}%`,
    }));
  }, []);

  const reset = useCallback(() => {
    setInfo(defaultDeviceInfo);
    modelConfigRef.current = null;
  }, []);

  return {
    info,
    modelConfig: modelConfigRef,
    parseOpts: parseOptsRef,
    handleCommand,
    setFormatType,
    updateBattery,
    reset,
  };
}
