import type { DeviceModelConfig } from "./types";
import { epocModel } from "./epoc";
import { epocPlusModel } from "./epocPlus";
import { insightModel } from "./insight";

/**
 * Model types lookup (from CyInterface.js)
 * 0: 'epoc', 1: 'epoc', 2: 'epoc',
 * 3: 'insight', 4: 'insight',
 * 5: 'epoc_plus', 6: 'epoc_plus', 7:'epoc_plus',
 * 8: 'epoc_flex'
 */
export const MODEL_TYPES: Record<number, string> = {
  0: "None",
  1: "Epoc-Research",
  2: "Epoc",
  3: "Insight (Research)",
  4: "Insight",
  5: "Epoc+ (Research)",
  6: "Epoc+",
  7: "EPOC+ (14-bit)",
  8: "Epoc-Flex",
};

const MODEL_FAMILY: Record<number, string> = {
  0: "epoc", 1: "epoc", 2: "epoc",
  3: "insight", 4: "insight",
  5: "epoc_plus", 6: "epoc_plus", 7: "epoc_plus",
  8: "epoc_plus",
};

const MODEL_CONFIGS: Record<string, DeviceModelConfig> = {
  epoc: epocModel,
  epoc_plus: epocPlusModel,
  insight: insightModel,
};

export function getModelConfig(keyModelId: number): DeviceModelConfig | null {
  const family = MODEL_FAMILY[keyModelId];
  if (!family) return null;
  return MODEL_CONFIGS[family] ?? null;
}

export function getModelFamily(keyModelId: number): string {
  return MODEL_FAMILY[keyModelId] ?? "epoc";
}

export function isInsightModel(keyModelId: number): boolean {
  return keyModelId === 3 || keyModelId === 4;
}

export function isEpocPlusModel(keyModelId: number): boolean {
  return keyModelId === 5 || keyModelId === 6 || keyModelId === 7;
}

/** Whether this model supports Floating Point / Raw Data format switching. */
export function supportsFormatSwitch(keyModelId: number): boolean {
  return isInsightModel(keyModelId) || isEpocPlusModel(keyModelId);
}

/**
 * Compute the backend-facing formatType number to send via changeFormat command.
 * Ported from CyInterface.js changeFormat().
 *
 * @param keyModel  - device key model id (3-7)
 * @param bluetooth - whether bluetooth mode is active
 * @param display   - user-selected display format: "float" or "raw"
 * @returns backend formatType (0-3)
 */
export function computeBackendFormat(
  keyModel: number,
  bluetooth: boolean,
  display: "float" | "raw",
): number {
  if (display === "float") {
    if (keyModel === 4 || keyModel === 3 || keyModel === 7) {
      return bluetooth ? 3 : 2;
    }
    // EPOC+ (5, 6)
    return 0;
  }
  // Raw Data
  if (keyModel === 4 || keyModel === 3) return 3;
  if (keyModel === 7) return bluetooth ? 3 : 1;
  // EPOC+ (5, 6)
  return 1;
}
