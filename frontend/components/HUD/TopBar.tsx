"use client";

import { usePolarisStore } from "@/lib/store";

function Telemetry({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div className="flex items-baseline gap-1.5">
      <span className="hud-header">{label}</span>
      <span className="text-sm font-semibold tabular-nums tracking-tight">
        {value}
      </span>
    </div>
  );
}

export function TopBar() {
  const vessel = usePolarisStore((s) => s.vessel);
  const time = usePolarisStore((s) => s.simTimeIso);
  const utc = new Date(time).toISOString().slice(11, 19);

  return (
    <header className="pointer-events-auto hud-panel flex items-center justify-between gap-6 px-4 py-2.5">
      <div className="flex items-center gap-3 min-w-[180px]">
        <div className="h-8 w-8 rounded-lg bg-accent/80 grid place-items-center font-black text-xs">
          P
        </div>
        <div>
          <div className="text-sm font-bold tracking-wide">POLARIS</div>
          <div className="hud-header">Antarctic DSS</div>
        </div>
      </div>
      <div className="flex items-center gap-6">
        <Telemetry label="LAT" value={vessel.lat.toFixed(4)} />
        <Telemetry label="LON" value={vessel.lon.toFixed(4)} />
        <Telemetry label="SOG" value={`${vessel.sogKnots.toFixed(1)} kn`} />
        <Telemetry label="COG" value={`${vessel.cogDeg.toFixed(0)}°`} />
        <Telemetry label="TIME" value={`${utc} UTC`} />
      </div>
      <div className="min-w-[180px] text-right hud-header">Settings</div>
    </header>
  );
}
