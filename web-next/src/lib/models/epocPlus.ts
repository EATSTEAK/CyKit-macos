import type {
  DeviceModelConfig,
  ChannelSample,
  ParseOptions,
  QualityUpdate,
} from "./types";
import { convertEpocPlus, getEpocQuality } from "./types";

const SENSOR_NAMES = ["AF3", "F7", "F3", "FC5", "T7", "P7", "O1", "O2", "P8", "T8", "FC6", "F4", "F8", "AF4"];
const SENSOR_DATA_INDICES = [4, 5, 2, 3, 6, 7, 8, 9, 10, 11, 14, 15, 12, 13];

const QUALITY_COUNTER_128: string[] = [
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

export const epocPlusModel: DeviceModelConfig = {
  id: "epoc_plus",
  displayName: "EPOC+",
  channelCount: 14,
  sampleRate: 256,
  sensorMap: {
    names: SENSOR_NAMES,
    dataIndices: SENSOR_DATA_INDICES,
  },
  qualityCounterMap: QUALITY_COUNTER_128,

  parseSample(contact: string[], opts: ParseOptions): ChannelSample[] {
    const samples: ChannelSample[] = [];

    if (contact[1] !== "16") return samples;

    if (opts.outputData || opts.formatType === 0) {
      // Floating Point mode (or Python pre-converted via outputdata)
      for (let i = 0; i < SENSOR_NAMES.length; i++) {
        const dataIdx = SENSOR_DATA_INDICES[i];
        const value = parseFloat(contact[dataIdx]) || 0;
        samples.push({ channelIndex: i, value });
      }
    } else {
      // Raw Data mode - need to convert pairs
      for (let i = 2; i < contact.length - 1; i += 2) {
        const channelIdx = (i - 2) / 2;
        if (channelIdx >= 14) break;
        const v1 = parseInt(contact[i], 10) || 0;
        const v2 = parseInt(contact[i + 1], 10) || 0;
        const value = convertEpocPlus(v1, v2);
        samples.push({ channelIndex: channelIdx, value });
      }
    }

    return samples;
  },

  calculateBattery(contact: string[], opts: ParseOptions): number | null {
    if (contact[1] !== "16") return null;

    const counter = parseInt(contact[0], 10);
    if (counter !== 127 && counter !== 255) return null;
    if (opts.noBattery || opts.noCounter) return null;

    const batteryPosition = opts.formatType === 0 ? 16 : 30;
    const rawValue = parseInt(contact[batteryPosition], 10);
    if (!rawValue) return null;

    // Detect 128Hz vs 256Hz mode
    const batteryMode = rawValue < 64 ? 0 : 117;
    const percent = (rawValue - batteryMode) * 1.612903;
    return Math.max(0, Math.min(100, Math.round(percent)));
  },

  parseQuality(contact: string[], opts: ParseOptions): QualityUpdate[] {
    const updates: QualityUpdate[] = [];
    const counter = parseInt(contact[0], 10);
    const sensorName = QUALITY_COUNTER_128[counter];
    if (!sensorName) return updates;

    let coreValue: number;
    let detailValue: number;

    if (opts.formatType === 0) {
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
