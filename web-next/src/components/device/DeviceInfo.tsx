import type { DeviceInfo as DeviceInfoType } from "../../hooks/useDeviceInfo";

interface Props {
  info: DeviceInfoType;
}

export function DeviceInfo({ info }: Props) {
  return (
    <div className="space-y-2 text-[11px]">
      <SectionHeader title="DEVICE" />
      <InfoRow label="Status" value={info.status} accent={info.status === "Connected"} />
      <InfoRow label="Headset" value={info.headset} />
      <InfoRow label="USB Name" value={info.device} />
      <InfoRow label="Serial" value={info.serial} />
      <InfoRow label="Key Model" value={info.keyModelDisplay} />
      <InfoRow label="Battery" value={info.battery} accent={info.battery !== "N/A"} />
    </div>
  );
}

function SectionHeader({ title }: { title: string }) {
  return (
    <div>
      <div className="text-text-dim text-[10px] tracking-widest mb-1">
        {title}
      </div>
      <div className="border-t border-border" />
    </div>
  );
}

function InfoRow({
  label,
  value,
  accent = false,
}: {
  label: string;
  value: string;
  accent?: boolean;
}) {
  return (
    <div className="flex justify-between">
      <span className="text-text-dim">{label}</span>
      <span className={accent ? "text-accent" : "text-text"}>{value}</span>
    </div>
  );
}
