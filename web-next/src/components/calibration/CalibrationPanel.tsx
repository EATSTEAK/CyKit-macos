interface Props {
  baselineEnabled: boolean;
  pyBaseline: boolean;
  onToggleBaseline: (enabled: boolean) => void;
  onTogglePyBaseline: (enabled: boolean) => void;
  onResetBaseline: () => void;
  scrollMode: boolean;
  onScrollModeChange: (enabled: boolean) => void;
  boldLine: boolean;
  onBoldLineChange: (enabled: boolean) => void;
}

export function CalibrationPanel({
  baselineEnabled,
  pyBaseline,
  onToggleBaseline,
  onTogglePyBaseline,
  onResetBaseline,
  scrollMode,
  onScrollModeChange,
  boldLine,
  onBoldLineChange,
}: Props) {
  return (
    <div className="space-y-4 p-4">
      <div>
        <div className="text-text-dim text-[10px] tracking-widest mb-1">CALIBRATION</div>
        <div className="border-t border-border mb-4" />

        <div className="space-y-3 text-[11px]">
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={baselineEnabled}
              onChange={(e) => onToggleBaseline(e.target.checked)}
            />
            <span>Baseline Correction</span>
          </label>

          <button
            onClick={onResetBaseline}
            className="w-full text-[11px] border-cyan text-cyan hover:bg-cyan hover:text-bg"
          >
            Reset Baseline
          </button>

          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={pyBaseline}
              onChange={(e) => onTogglePyBaseline(e.target.checked)}
            />
            <span>Python Baseline</span>
          </label>
        </div>
      </div>

      <div>
        <div className="text-text-dim text-[10px] tracking-widest mb-1">DISPLAY</div>
        <div className="border-t border-border mb-4" />

        <div className="space-y-3 text-[11px]">
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={scrollMode}
              onChange={(e) => onScrollModeChange(e.target.checked)}
            />
            <span>Scroll Mode</span>
          </label>

          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={boldLine}
              onChange={(e) => onBoldLineChange(e.target.checked)}
            />
            <span>Bold Line</span>
          </label>
        </div>
      </div>
    </div>
  );
}
