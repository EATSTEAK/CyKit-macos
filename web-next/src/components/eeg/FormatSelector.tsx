interface Props {
  value: "float" | "raw";
  onChange: (value: "float" | "raw") => void;
}

/**
 * Format selector: switch between Floating Point and Raw Data modes.
 * Visible only for Insight / EPOC+ models.
 */
export function FormatSelector({ value, onChange }: Props) {
  return (
    <div className="flex items-center gap-2">
      <span className="text-text-dim text-[10px] w-[72px]">Format:</span>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value as "float" | "raw")}
        className="flex-1 bg-bg text-text text-[11px] border border-border px-1 py-0.5"
      >
        <option value="float">Floating Point</option>
        <option value="raw">Raw Data</option>
      </select>
    </div>
  );
}
