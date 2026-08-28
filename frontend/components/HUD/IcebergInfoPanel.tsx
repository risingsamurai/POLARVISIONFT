"use client";

import { usePolarisStore } from "@/lib/store";

export function IcebergInfoPanel() {
  const id = usePolarisStore((s) => s.selectedIcebergId);
  const iceberg = usePolarisStore((s) =>
    s.icebergs.find((i) => i.id === id)
  );

  return (
    <section className="hud-panel p-3.5 w-72 bg-black/40 backdrop-blur-md border border-white/10 rounded-xl text-white shadow-xl">
      <div className="flex items-center justify-between mb-2.5">
        <h2 className="hud-header text-[10px] font-bold uppercase tracking-[0.18em] text-white/50">
          Iceberg Telemetry
        </h2>
        {iceberg && (
          <span
            className={`rounded-full px-2 py-0.5 text-[9px] font-bold uppercase tracking-wide ${
              iceberg.highRisk
                ? "bg-red-500/20 text-red-300 border border-red-500/30"
                : "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
            }`}
          >
            {iceberg.status}
          </span>
        )}
      </div>

      {!iceberg ? (
        <div className="py-4 text-center">
          <p className="text-xs text-white/40">Select an iceberg in the 3D scene</p>
          <p className="text-[10px] text-white/25 mt-0.5">Click any ice mass to inspect</p>
        </div>
      ) : (
        <dl className="grid grid-cols-[auto_1fr] gap-x-3 gap-y-1.5 text-xs">
          <dt className="text-white/45 text-[11px]">ID</dt>
          <dd className="font-semibold font-mono text-cyan-300 tabular-nums">
            {iceberg.id}
          </dd>
          <dt className="text-white/45 text-[11px]">Designation</dt>
          <dd className="font-semibold text-white/90">{iceberg.name}</dd>
          <dt className="text-white/45 text-[11px]">Diameter</dt>
          <dd className="tabular-nums font-mono text-white/90">
            {iceberg.diameterNm.toFixed(1)} NM
          </dd>
          <dt className="text-white/45 text-[11px]">Size Class</dt>
          <dd className="uppercase text-[11px] font-semibold text-sky-200">
            {iceberg.sizeClass.replace("_", " ")}
          </dd>
          <dt className="text-white/45 text-[11px]">Coordinates</dt>
          <dd className="tabular-nums font-mono text-[11px] text-white/80">
            {iceberg.lat.toFixed(3)}° S, {Math.abs(iceberg.lon).toFixed(3)}° W
          </dd>
          <dt className="text-white/45 text-[11px]">Drift Heading</dt>
          <dd className="tabular-nums font-mono text-[11px] text-white/80">
            {iceberg.headingDeg.toFixed(0)}°
          </dd>
        </dl>
      )}
    </section>
  );
}

