"use client";

import { ExportPdfButton } from "@/components/HUD/ExportPdfButton";
import { selectLockedRoute, usePolarisStore } from "@/lib/store";

export function RouteInfoPanel() {
  const route = usePolarisStore(selectLockedRoute);
  const recalculate = usePolarisStore((s) => s.recalculateRoute);
  const version = usePolarisStore((s) => s.routeVersion);

  return (
    <section className="hud-panel p-3.5 w-72 bg-black/40 backdrop-blur-md border border-white/10 rounded-xl text-white shadow-xl">
      <div className="flex items-center justify-between mb-2.5">
        <h2 className="hud-header text-[10px] font-bold uppercase tracking-[0.18em] text-white/50">
          Navigation Plan
        </h2>
        <span className="text-[10px] font-mono text-cyan-400 bg-cyan-500/10 px-2 py-0.5 rounded border border-cyan-500/20">
          Rev {version}
        </span>
      </div>

      <dl className="grid grid-cols-[auto_1fr] gap-x-3 gap-y-1.5 text-xs mb-3.5">
        <dt className="text-white/45 text-[11px]">Selected Profile</dt>
        <dd className="font-semibold text-white/90 capitalize">{route.name}</dd>
        <dt className="text-white/45 text-[11px]">Route Distance</dt>
        <dd className="tabular-nums font-mono text-white/90 font-semibold">
          {route.distanceNm.toFixed(1)} NM
        </dd>
        <dt className="text-white/45 text-[11px]">Estimated ETA</dt>
        <dd className="tabular-nums font-mono text-white/90">
          {route.etaHours.toFixed(1)} hrs
        </dd>
        <dt className="text-white/45 text-[11px]">Est. Fuel Burn</dt>
        <dd className="tabular-nums font-mono text-white/90">
          {route.fuelMt.toFixed(1)} MT
        </dd>
        <dt className="text-white/45 text-[11px]">Risk Factor</dt>
        <dd className="tabular-nums font-mono text-emerald-400 font-semibold">
          {(route.riskScore * 100).toFixed(0)}%
        </dd>
      </dl>

      <div className="space-y-2">
        <button
          type="button"
          onClick={recalculate}
          className="w-full rounded-lg bg-cyan-600 hover:bg-cyan-500 active:bg-cyan-700 transition-all text-white px-3 py-2 text-xs font-bold uppercase tracking-wider shadow-md shadow-cyan-600/30"
        >
          Recalculate Route
        </button>
        <ExportPdfButton />
      </div>
    </section>
  );
}

