import type { QualityLevel } from "../../lib/models/types";
import { QUALITY_COLORS } from "../../lib/models/types";

interface Props {
  sensorNames: string[];
  quality: Record<string, QualityLevel>;
}

export function SensorQuality({ sensorNames, quality }: Props) {
  return (
    <div className="space-y-2">
      <div className="text-text-dim text-[10px] tracking-widest">QUALITY</div>
      <div className="border-t border-border" />
      <div className="flex flex-wrap gap-1">
        {sensorNames.map((name) => {
          const level = quality[name] ?? "black";
          return (
            <QualityDot key={name} name={name} level={level} />
          );
        })}
      </div>
    </div>
  );
}

function QualityDot({ name, level }: { name: string; level: QualityLevel }) {
  const color = QUALITY_COLORS[level];

  return (
    <div className="flex flex-col items-center gap-0.5" title={`${name}: ${level}`}>
      <div
        className="w-4 h-4 border-2 transition-colors duration-200"
        style={{ borderColor: color, backgroundColor: `${color}33` }}
      />
      <span className="text-[8px] text-text-dim leading-none">{name}</span>
    </div>
  );
}
