"use client";

import { usePolarisStore } from "@/lib/store";

export function DataRealityBadge() {
  const reality = usePolarisStore((s) => s.dataReality);
  const rows = [
    { name: "NSIDC", ...reality.nsidc },
    { name: "BYU/NIC", ...reality.byu },
    { name: "ERA5", ...reality.era5 },
  ];

  return (
    <section className="hud-panel p-2 w-64 text-[10px]">
      <h2 className="hud-header mb-1">Data Reality</h2>
      <ul className="space-y-0.5">
        {rows.map((r) => (
          <li key={r.name} className="flex items-center justify-between gap-2">
            <span>{r.name}</span>
            <span
              className={
                r.status === "LIVE" ? "text-emerald-400 font-bold" : "text-amber-300 font-bold"
              }
            >
              {r.status}
            </span>
          </li>
        ))}
      </ul>
    </section>
  );
}
