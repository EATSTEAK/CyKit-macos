import type {
  DeviceModelConfig,
  ChannelSample,
  ParseOptions,
  QualityUpdate,
} from "./types";
import { getEpocQuality } from "./types";

const SENSOR_NAMES = ["AF3", "F7", "F3", "FC5", "T7", "P7", "O1", "O2", "P8", "T8", "FC6", "F4", "F8", "AF4"];
const SENSOR_DATA_INDICES = [4, 5, 2, 3, 6, 7, 8, 9, 10, 11, 14, 15, 12, 13];

// Quality counter map for EPOC 128Hz
const QUALITY_COUNTER: string[] = [
  "F3", "FC5", "AF3", "F7", "T7", "P7", "O1", "O2", "P8", "T8", "F8", "AF4", "FC6", "F4",
  "F8", "AF4", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "",
  "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "",
  "", "F3", "FC5", "AF3", "F7", "T7", "P7", "O1", "O2", "P8", "T8", "F8", "AF4", "FC6", "F4",
  "F8", "AF4", "FC6", "F4", "F8", "AF4", "FC6", "F4", "F8", "AF4", "FC6", "F4",
  "F8", "AF4", "FC6", "F4", "F8", "AF4", "FC6", "F4", "F8", "AF4", "FC6", "F4",
  "F8", "AF4", "FC6", "F4", "F8", "AF4", "FC6", "F4", "F8", "AF4", "FC6", "F4",
  "F8", "AF4", "FC6", "F4", "F8", "AF4", "FC6", "F4", "F8", "AF4", "FC6", "F4",
  "F8", "",
];

export const epocModel: DeviceModelConfig = {
  id: "epoc",
  displayName: "EPOC",
  channelCount: 14,
  sampleRate: 128,
  sensorMap: {
    names: SENSOR_NAMES,
    dataIndices: SENSOR_DATA_INDICES,
  },
  qualityCounterMap: QUALITY_COUNTER,

  parseSample(contact: string[], _opts: ParseOptions): ChannelSample[] {
    const samples: ChannelSample[] = [];
    for (let i = 0; i < SENSOR_NAMES.length; i++) {
      const dataIdx = SENSOR_DATA_INDICES[i] - 1; // convert 1-based to 0-based
      const value = Math.abs(parseFloat(contact[dataIdx]) || 0);
      samples.push({ channelIndex: i, value });
    }
    return samples;
  },

  calculateBattery(contact: string[]): number | null {
    const counter = parseInt(contact[0], 10);
    if (counter === 127) {
      // Battery is calculated on counter value 127
      // Battery value is at index 0 of the next packet
      const rawBattery = parseInt(contact[0], 10);
      const percent = ((rawBattery - 255 + 31) * 3.23);
      return Math.max(0, Math.min(100, Math.round(percent)));
    }
    return null;
  },

  parseQuality(contact: string[], opts: ParseOptions): QualityUpdate[] {
    const updates: QualityUpdate[] = [];
    const counter = parseInt(contact[0], 10);
    const sensorName = QUALITY_COUNTER[counter];
    if (!sensorName) return updates;

    let coreValue: number;
    let detailValue: number;

    if (opts.formatType === 0) {
      // Floating Point
      coreValue = parseFloat(contact[17]) || 0;
      detailValue = parseFloat(contact[16]) || 0;
    } else {
      coreValue = parseFloat(contact[31]) || 0;
      detailValue = parseFloat(contact[30]) || 0;
    }

    updates.push({
      sensorName,
      level: getEpocQuality(coreValue, detailValue),
    });

    return updates;
  },
};
