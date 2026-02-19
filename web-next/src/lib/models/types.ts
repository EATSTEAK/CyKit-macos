/** Color palette for EEG channels */
export const CHANNEL_COLORS = [
  "#ff7f7f", "#ffbe7f", "#ffdf7f", "#dfff7f", "#a0ff7f", "#7fffdf", "#7fdfff",
  "#7fa0ff", "#a07fff", "#df7fff", "#ff7fdf", "#ff7fa0", "#ff7f7f", "#fdff7f",
] as const;

/** Quality indicator colors */
export const QUALITY_COLORS = {
  black: "#333333",
  red: "#ff0000",
  orange: "#ee5000",
  green: "#66ea8d",
} as const;

export type QualityLevel = "black" | "red" | "orange" | "green";

export interface SensorMap {
  /** Display names for sensors (e.g. ["AF3", "F7", ...]) */
  names: string[];
  /** Data index mapping for each sensor name */
  dataIndices: number[];
}

export interface DeviceModelConfig {
  id: string;
  displayName: string;
  channelCount: number;
  sampleRate: number;
  sensorMap: SensorMap;
  /** Optional bluetooth variant sensor mapping */
  btSensorMap?: SensorMap;
  /**
   * Parse a CSV data line into per-channel values ready for the ring buffer.
   * Returns an array of [channelIndex, value] pairs.
   */
  parseSample: (
    contact: string[],
    opts: ParseOptions,
  ) => ChannelSample[];
  /** Calculate battery percentage from a data line */
  calculateBattery: (contact: string[], opts: ParseOptions) => number | null;
  /** Determine sensor quality from a data line */
  parseQuality: (contact: string[], opts: ParseOptions) => QualityUpdate[];
  /** Quality counter map: counter value → sensor name */
  qualityCounterMap: string[];
}

export interface ParseOptions {
  formatType: number; // 0=float, 1=raw
  noCounter: boolean;
  noBattery: boolean;
  bluetooth: boolean;
  /** Python backend already converted data to floating point (outputdata flag) */
  outputData: boolean;
  delimiter: string;
}

export interface ChannelSample {
  channelIndex: number;
  value: number;
}

export interface QualityUpdate {
  sensorName: string;
  level: QualityLevel;
}

/**
 * Convert raw EPOC+ 14-bit packed values to microvolts.
 * Ported from CyInterface.js convertEPOC_PLUS()
 */
export function convertEpocPlus(value1: number, value2: number): number {
  return (value1 * 0.128205128205129 + 4201.02564096001) + ((value2 - 128) * 32.82051289);
}

/**
 * Determine quality level from core_value and detail_value (EPOC/EPOC+).
 * Ported from CyInterface.js set_quality()
 */
export function getEpocQuality(coreValue: number, detailValue: number): QualityLevel {
  if (coreValue > 0) {
    if (detailValue < 129) {
      return coreValue > 1 ? "green" : "orange";
    }
    return "green";
  }
  if (detailValue > 158) return "orange";
  if (detailValue > 49) return "red";
  return "black";
}

/**
 * Determine quality level for Insight USB.
 * Ported from CyInterface.js set_insight_quality()
 */
export function getInsightUsbQuality(coreValue: number, detailValue: number): QualityLevel {
  if (coreValue > 2) {
    return coreValue < 6 ? "orange" : "green";
  }
  if (coreValue > 0 && detailValue > 30) return "orange";
  if (detailValue > 49) return "red";
  return "black";
}

/**
 * Determine quality level for Insight Bluetooth.
 */
export function getInsightBtQuality(coreValue: number): QualityLevel {
  if (coreValue < 50) return "black";
  if (coreValue < 160) return "red";
  if (coreValue < 250) return "orange";
  return "green";
}
