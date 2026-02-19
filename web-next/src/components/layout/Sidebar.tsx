import { DeviceInfo } from "../device/DeviceInfo";
import { SensorQuality } from "../device/SensorQuality";
import { ResolutionSlider } from "../eeg/ResolutionSlider";
import { FormatSelector } from "../eeg/FormatSelector";
import type { DeviceInfo as DeviceInfoType } from "../../hooks/useDeviceInfo";
import type { QualityLevel } from "../../lib/models/types";

interface Props {
  deviceInfo: DeviceInfoType;
  sensorNames: string[];
  quality: Record<string, QualityLevel>;
  resolution: number;
  onResolutionChange: (value: number) => void;
  scrollMode: boolean;
  onScrollModeChange: (enabled: boolean) => void;
  showFormatSelector: boolean;
  displayFormat: "float" | "raw";
  onFormatChange: (format: "float" | "raw") => void;
}

export function Sidebar({
  deviceInfo,
  sensorNames,
  quality,
  resolution,
  onResolutionChange,
  scrollMode,
  onScrollModeChange,
  showFormatSelector,
  displayFormat,
  onFormatChange,
}: Props) {
  return (
    <aside className="w-56 border-r border-border bg-panel flex flex-col shrink-0 overflow-y-auto">
      <div className="p-3 space-y-4">
        <DeviceInfo info={deviceInfo} />

        {sensorNames.length > 0 && (
          <SensorQuality sensorNames={sensorNames} quality={quality} />
        )}

        <div className="space-y-2">
          <div className="text-text-dim text-[10px] tracking-widest">CONTROLS</div>
          <div className="border-t border-border" />

          <label className="flex items-center gap-2 cursor-pointer text-[11px]">
            <input
              type="checkbox"
              checked={scrollMode}
              onChange={(e) => onScrollModeChange(e.target.checked)}
            />
            <span>Scroll</span>
          </label>

          <ResolutionSlider
            value={resolution}
            onChange={onResolutionChange}
          />

          {showFormatSelector && (
            <FormatSelector
              value={displayFormat}
              onChange={onFormatChange}
            />
          )}
        </div>
      </div>
    </aside>
  );
}
