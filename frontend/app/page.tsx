"use client";

import dynamic from "next/dynamic";
import Link from "next/link";
import { DataRealityBadge } from "@/components/HUD/DataRealityBadge";
import { usePolarisStore } from "@/lib/store";

const OverviewMap = dynamic(
  () => import("@/components/Map/OverviewMap").then((m) => m.OverviewMap),
  { ssr: false }
);

export default function HomePage() {
  const routes = usePolarisStore((s) => s.routes);
  const lock = usePolarisStore((s) => s.lockRoute);
  const locked = usePolarisStore((s) => s.lockedRouteId);

  return (
    <main className="h-screen w-screen relative bg-slate-950">
      <OverviewMap />
      <div className="pointer-events-none absolute inset-0 p-4 flex flex-col justify-between">
        <div className="flex justify-between">
          <div className="pointer-events-auto hud-panel p-4 max-w-md">
            <p className="hud-header">SIH PS 26059 · MoES / NCPOR</p>
            <h1 className="text-2xl font-bold">POLARIS Overview</h1>
            <p className="text-xs text-white/70 mt-1">
              Click the map to set a destination. Three A* routes overlay. Lock one, then open the 3D simulator.
            </p>
            <Link
              href="/simulation"
              className="inline-flex mt-3 rounded-lg bg-accent px-3 py-2 text-xs font-bold uppercase"
            >
              3D simulator
            </Link>
          </div>
          <div className="pointer-events-auto">
            <DataRealityBadge />
          </div>
        </div>
        <div className="pointer-events-auto hud-panel p-3 self-center min-w-[520px]">
          <h2 className="hud-header mb-2">Route comparison</h2>
          <div className="grid grid-cols-3 gap-2">
            {routes.map((r) => (
              <button
                key={r.id}
                type="button"
                onClick={() => lock(r.id)}
                className={`rounded-lg p-2 text-left text-xs border ${
                  locked === r.id ? "border-accent bg-accent/20" : "border-white/10"
                }`}
              >
                <div className="font-bold uppercase">{r.name}</div>
                <div className="tabular-nums">{r.distanceNm} NM · {r.etaHours} h</div>
                <div>Risk {r.riskScore} · {r.fuelMt} MT</div>
              </button>
            ))}
          </div>
        </div>
      </div>
    </main>
  );
}
