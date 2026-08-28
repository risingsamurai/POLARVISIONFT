"use client";

import { usePolarisStore } from "@/lib/store";

export function DetectionLog() {
  const detections = usePolarisStore((s) => s.detections);
  return (
    <section className="hud-panel p-3 w-72 max-h-40 overflow-auto">
      <h2 className="hud-header mb-2">Onboard Detection</h2>
      {detections.length === 0 ? (
        <p className="text-xs text-white/40">Scanner idle</p>
      ) : (
        <ul className="space-y-1 text-[11px]">
          {detections.slice(-6).reverse().map((d, i) => (
            <li key={`${d.name}-${i}`}>
              <span className="font-semibold">{d.name}</span>{" "}
              {(d.confidence * 100).toFixed(0)}% · {d.distanceNm} nm
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
