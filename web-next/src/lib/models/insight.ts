import type {
  DeviceModelConfig,
  ChannelSample,
  ParseOptions,
  QualityUpdate,
} from "./types";
import { convertEpocPlus, getInsightUsbQuality, getInsightBtQuality } from "./types";

const SENSOR_NAMES = ["AF3", "T7", "Pz", "T8", "AF4"];
const SENSOR_DATA_INDICES = [5, 9, 13, 23, 27];
const BT_SENSOR_DATA_INDICES = [1, 3, 5, 7, 9];

const QUALITY_COUNTER: string[] = (() => {
  const arr = new Array(128).fill("");
  arr[2] = "AF3"; arr[4] = "T7"; arr[6] = "Pz"; arr[9] = "T8"; arr[11] = "AF4";
  arr[64] = "AF3"; arr[66] = "T7"; arr[68] = "Pz"; arr[71] = "T8"; arr[73] = "AF4";
  arr[107] = "AF4";
  return arr;
})();

export const insightModel: DeviceModelConfig = {
  id: "insight",
  displayName: "Insight",
  channelCount: 5,
  sampleRate: 128,
  sensorMap: {
    names: SENSOR_NAMES,
    dataIndices: SENSOR_DATA_INDICES,
  },
  btSensorMap: {
    names: SENSOR_NAMES,
    dataIndices: BT_SENSOR_DATA_INDICES,
  },
  qualityCounterMap: QUALITY_COUNTER,

  parseSample(contact: string[], opts: ParseOptions): ChannelSample[] {
    const samples: ChannelSample[] = [];
    const isBT = opts.bluetooth;
    const indices = isBT ? BT_SENSOR_DATA_INDICES : SENSOR_DATA_INDICES;

    for (let i = 0; i < SENSOR_NAMES.length; i++) {
      const dataIdx = indices[i];

      let value: number;
      if (opts.outputData || opts.formatType === 0) {
        // Python already converted to floating point µV — use directly
        value = parseFloat(contact[dataIdx]) || 0;
      } else {
        // Raw data — need to convert pair
        const v1 = parseFloat(contact[dataIdx]) || 0;
        const v2 = parseFloat(contact[dataIdx + 1]) || 0;
        value = convertEpocPlus(v2, v1);
      }

      samples.push({ channelIndex: i, value });
    }

    return samples;
  },

  calculateBattery(contact: string[]): number | null {
    const counter = parseInt(contact[0], 10);
    if (counter === 127) {
      const percent = ((counter - 245 + 26) * 3.85);
      return Math.max(0, Math.min(100, Math.round(percent)));
    }
    return null;
  },

  parseQuality(contact: string[], opts: ParseOptions): QualityUpdate[] {
    const updates: QualityUpdate[] = [];
    const counter = parseInt(contact[0], 10);

    if (counter >= 128) return updates;

    const sensorName = QUALITY_COUNTER[counter];
    if (!sensorName) return updates;

    if (opts.bluetooth) {
      const coreValue = parseInt(contact[11], 10) || 0;
      updates.push({
        sensorName,
        level: getInsightBtQuality(coreValue),
      });
    } else {
      const coreValue = parseInt(contact[15], 10) || 0;
      const detailValue = parseInt(contact[16], 10) || 0;
      updates.push({
        sensorName,
        level: getInsightUsbQuality(coreValue, detailValue),
      });
    }

    return updates;
  },
};
