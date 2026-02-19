import { useRef, useCallback } from "react";
import { MultiChannelRingBuffer } from "../lib/ringBuffer";
import type { DeviceModelConfig, ParseOptions, QualityLevel } from "../lib/models/types";
import type { DataMessage } from "../lib/protocol";

const MAX_CHANNELS = 14;
const SAMPLES_PER_CHANNEL = 1024; // ~8 sec at 128Hz

export interface QualityMap {
  [sensorName: string]: QualityLevel;
}

export function useEEGData() {
  const ringBufferRef = useRef(
    new MultiChannelRingBuffer(MAX_CHANNELS, SAMPLES_PER_CHANNEL),
  );
  const qualityRef = useRef<QualityMap>({});
  const baselineRef = useRef<number[]>(new Array(MAX_CHANNELS).fill(0));
  const baselineInitRef = useRef(false);

  const handleData = useCallback(
    (
      msg: DataMessage,
      modelConfig: DeviceModelConfig | null,
      parseOpts: ParseOptions,
    ) => {
      if (!modelConfig) return;

      const delimiter = parseOpts.delimiter || ",";
      const contact = msg.raw.split(delimiter);

      // If no counter mode, prepend default counter + data type
      if (parseOpts.noCounter) {
        contact.unshift("0", "16");
      }

      // Parse EEG samples and push to ring buffer
      const samples = modelConfig.parseSample(contact, parseOpts);
      for (const { channelIndex, value } of samples) {
        ringBufferRef.current.pushSample(channelIndex, value);
      }

      // Update quality
      const qualityUpdates = modelConfig.parseQuality(contact, parseOpts);
      for (const { sensorName, level } of qualityUpdates) {
        qualityRef.current[sensorName] = level;
      }

      // Calculate battery if applicable
      const battery = modelConfig.calculateBattery(contact, parseOpts);

      return battery;
    },
    [],
  );

  const resetBaseline = useCallback(() => {
    baselineRef.current.fill(0);
    baselineInitRef.current = false;
  }, []);

  const updateBaseline = useCallback(() => {
    const rb = ringBufferRef.current;
    for (let ch = 0; ch < rb.channelCount; ch++) {
      const latest = rb.getChannel(ch).latest();
      if (!baselineInitRef.current) {
        baselineRef.current[ch] = latest;
      } else {
        baselineRef.current[ch] =
          (baselineRef.current[ch] + latest) / 2;
      }
    }
    baselineInitRef.current = true;
  }, []);

  const clear = useCallback(() => {
    ringBufferRef.current.clear();
    qualityRef.current = {};
    resetBaseline();
  }, [resetBaseline]);

  return {
    ringBuffer: ringBufferRef,
    quality: qualityRef,
    baseline: baselineRef,
    handleData,
    resetBaseline,
    updateBaseline,
    clear,
  };
}
