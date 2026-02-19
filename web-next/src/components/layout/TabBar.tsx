export type TabId = "eeg" | "calibration" | "recording";

interface Props {
  activeTab: TabId;
  onChange: (tab: TabId) => void;
}

const TABS: { id: TabId; label: string }[] = [
  { id: "eeg", label: "EEG" },
  { id: "calibration", label: "Calibration" },
  { id: "recording", label: "Recording" },
];

export function TabBar({ activeTab, onChange }: Props) {
  return (
    <div className="flex border-b border-border bg-panel shrink-0">
      {TABS.map(({ id, label }) => (
        <button
          key={id}
          onClick={() => onChange(id)}
          className={`
            px-4 py-1.5 text-[11px] tracking-wider border-b-2 border-l border-r border-t-0 transition-colors
            ${
              activeTab === id
                ? "border-b-accent text-accent bg-bg border-l-border border-r-border"
                : "border-b-transparent text-text-dim border-l-transparent border-r-transparent hover:text-text hover:bg-bg/50"
            }
          `}
        >
          {label}
        </button>
      ))}
    </div>
  );
}
