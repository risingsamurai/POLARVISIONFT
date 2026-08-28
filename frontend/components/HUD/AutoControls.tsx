"use client";

import { fetchRoutes } from "@/lib/api";
import { usePolarisStore } from "@/lib/store";

export function AutoControls() {
  const auto = usePolarisStore((s) => s.autoMode);
  const setAuto = usePolarisStore((s) => s.setAutoMode);
  const vessel = usePolarisStore((s) => s.vessel);
  const dest = usePolarisStore((s) => s.destination);
  const setRoutes = usePolarisStore((s) => s.setRoutes);
  const lock = usePolarisStore((s) => s.lockRoute);
  const pushAlert = usePolarisStore((s) => s.pushAlert);

  return (
    <section className="hud-panel p-3 w-72 space-y-2">
      <h2 className="hud-header">Mission Control</h2>
      <button
        type="button"
        onClick={async () => {
          try {
            const data = await fetchRoutes(
              [vessel.lat, vessel.lon],
              [dest.lat, dest.lon]
            );
            if (data.routes?.length) {
              setRoutes(data.routes);
              lock("balanced");
              pushAlert("INFO", "Iceberg trajectory updated, route recalculating");
            }
          } catch {
            pushAlert("WARNING", "Route API unreachable — using onboard A* mock");
          }
          setAuto(!auto);
        }}
        className={`w-full rounded-lg px-3 py-2 text-xs font-bold uppercase ${
          auto ? "bg-emerald-600" : "bg-accent"
        }`}
      >
        {auto ? "Autonomous ON — override" : "Engage autonomous"}
      </button>
    </section>
  );
}
