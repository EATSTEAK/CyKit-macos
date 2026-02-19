interface Props {
  sensorNames: string[];
  enabledChannels: boolean[];
  onChange: (index: number, enabled: boolean) => void;
  onToggleAll: (enabled: boolean) => void;
}

export function ChannelSelector({
  sensorNames,
  enabledChannels,
  onChange,
  onToggleAll,
}: Props) {
  const allChecked = enabledChannels.every(Boolean);

  return (
    <div className="flex flex-wrap gap-x-3 gap-y-1 items-center text-[11px]">
      <label className="flex items-center gap-1 cursor-pointer text-text-dim">
        <input
          type="checkbox"
          checked={allChecked}
          onChange={(e) => onToggleAll(e.target.checked)}
        />
        ALL
      </label>
      <span className="text-border-light">|</span>
      {sensorNames.map((name, i) => (
        <label key={name} className="flex items-center gap-1 cursor-pointer">
          <input
            type="checkbox"
            checked={enabledChannels[i] ?? true}
            onChange={(e) => onChange(i, e.target.checked)}
          />
          <span style={{ color: getChannelColor(i) }}>{name}</span>
        </label>
      ))}
    </div>
  );
}

function getChannelColor(index: number): string {
  const colors = [
    "#ff7f7f", "#ffbe7f", "#ffdf7f", "#dfff7f", "#a0ff7f", "#7fffdf", "#7fdfff",
    "#7fa0ff", "#a07fff", "#df7fff", "#ff7fdf", "#ff7fa0", "#ff7f7f", "#fdff7f",
  ];
  return colors[index % colors.length];
}
