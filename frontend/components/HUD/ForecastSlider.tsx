"use client";

import { usePolarisStore } from "@/lib/store";

export function ForecastSlider() {
  const day = usePolarisStore((s) => s.forecastDay);
  const setDay = usePolarisStore((s) => s.setForecastDay);
  return (
    <section className="hud-panel p-3 w-64">
      <h2 className="hud-header mb-2">IceNet 7-day</h2>
      <input
        type="range"
        min={1}
        max={7}
        value={day}
        onChange={(e) => setDay(Number(e.target.value))}
        className="w-full"
      />
      <p className="text-xs tabular-nums mt-1">Forecast day {day}</p>
    </section>
  );
}
