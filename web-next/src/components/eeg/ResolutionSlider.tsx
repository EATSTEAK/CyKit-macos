interface Props {
  value: number;
  onChange: (value: number) => void;
}

/**
 * Resolution slider: controls amplitude scaling of EEG waveforms.
 * Range: 1% – 500% (0.01 – 5.0 internally).
 */
export function ResolutionSlider({ value, onChange }: Props) {
  const percent = Math.round(value * 100);

  return (
    <div className="flex items-center gap-2">
      <span className="text-text-dim text-[10px] w-[72px]">Resolution:</span>
      <input
        type="range"
        min={1}
        max={500}
        value={percent}
        onChange={(e) => onChange(parseInt(e.target.value, 10) * 0.01)}
        className="flex-1"
      />
      <span className="text-accent text-[10px] w-10 text-right font-medium">
        {percent}%
      </span>
    </div>
  );
}
