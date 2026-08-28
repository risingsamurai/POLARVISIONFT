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
    <section className="hud-panel p-2.5 w-64 text-[10px] bg-slate-900/90 border border-white/10 rounded-xl shadow-xl">
      <h2 className="hud-header mb-1.5 text-slate-400 font-semibold tracking-wider uppercase">Data Reality</h2>
      <ul className="space-y-1.5">
        {rows.map((r) => (
          <li key={r.name} className="flex flex-col gap-0.5 border-b border-white/5 pb-1 last:border-0 last:pb-0">
            <div className="flex items-center justify-between gap-2">
              <span className="font-medium text-slate-300">{r.name}</span>
              <span
                className={
                  r.status === "LIVE" ? "text-emerald-400 font-bold" : "text-amber-300 font-bold"
                }
              >
                {r.status}
              </span>
            </div>
            {r.status === "FALLBACK" && r.reason && (
              <span className="text-[9px] text-slate-400 leading-tight italic break-words">
                {r.reason}
              </span>
            )}
          </li>
        ))}
      </ul>
    </section>
  );
}
