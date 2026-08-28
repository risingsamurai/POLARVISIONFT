"use client";

import { ICE_LEVELS } from "@/lib/mockData";

export function IceLevelLegend() {
  return (
    <section className="hud-panel p-3.5 w-64 bg-black/40 backdrop-blur-md border border-white/10 rounded-xl text-white shadow-xl">
      <h2 className="hud-header mb-3 text-[10px] font-bold uppercase tracking-[0.18em] text-white/50">
        Ice Level
      </h2>
      <ul className="space-y-2">
        {ICE_LEVELS.map((row) => (
          <li key={row.label} className="flex items-center justify-between text-xs">
            <div className="flex items-center gap-2.5">
              <span
                className="h-3 w-5 rounded-sm border border-white/20 shadow-inner"
                style={{ background: row.color }}
              />
              <span className="font-semibold uppercase tracking-wider text-[11px] text-white/90">
                {row.label}
              </span>
            </div>
            <span className="tabular-nums text-white/50 text-[11px] font-mono">
              {row.range}
            </span>
          </li>
        ))}
      </ul>
    </section>
  );
}

