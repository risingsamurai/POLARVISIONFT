"use client";

import { useEffect } from "react";
import { usePolarisStore } from "@/lib/store";

const COLOR: Record<string, string> = {
  CRITICAL: "bg-red-600/80",
  WARNING: "bg-amber-500/80",
  INFO: "bg-sky-500/80",
  CLEAR: "bg-emerald-600/80",
};

function beep() {
  const ctx = new AudioContext();
  const osc = ctx.createOscillator();
  const gain = ctx.createGain();
  osc.frequency.value = 880;
  gain.gain.value = 0.08;
  osc.connect(gain);
  gain.connect(ctx.destination);
  osc.start();
  osc.stop(ctx.currentTime + 0.18);
}

const DEMO: { tier: string; message: string }[] = [
  { tier: "CRITICAL", message: "Vessel within 5nm of an iceberg" },
  { tier: "WARNING", message: "Ice concentration ahead exceeds 70%" },
  { tier: "INFO", message: "Iceberg trajectory updated, route recalculating" },
  { tier: "CLEAR", message: "All hazards outside safe radius" },
];

export function AlertBanner() {
  const alerts = usePolarisStore((s) => s.alerts);
  const soundOn = usePolarisStore((s) => s.soundOn);
  const setSoundOn = usePolarisStore((s) => s.setSoundOn);
  const pushAlert = usePolarisStore((s) => s.pushAlert);
  const latest = alerts[alerts.length - 1];

  useEffect(() => {
    if (!latest || !soundOn) return;
    if (latest.tier === "CRITICAL" || latest.tier === "WARNING") {
      try {
        beep();
      } catch {
        /* autoplay policies */
      }
    }
  }, [latest, soundOn]);

  return (
    <div className="pointer-events-auto flex flex-wrap items-center gap-2">
      {latest && (
        <div
          className={`rounded-xl px-4 py-2 text-xs font-bold uppercase tracking-wide ${
            COLOR[latest.tier] || "bg-black/50"
          }`}
        >
          {latest.tier}: {latest.message}
        </div>
      )}
      <button
        type="button"
        className="hud-panel px-2 py-1 text-[10px] font-bold uppercase"
        onClick={() => setSoundOn(!soundOn)}
      >
        Sound {soundOn ? "ON" : "OFF"}
      </button>
      <button
        type="button"
        className="hud-panel px-2 py-1 text-[10px] font-bold uppercase"
        onClick={() => {
          const header = "tier,message,ts";
          const rows = alerts.map((a) => `${a.tier},"${a.message}",${a.ts}`);
          const blob = new Blob([[header, ...rows].join("\n")], {
            type: "text/csv",
          });
          const url = URL.createObjectURL(blob);
          const a = document.createElement("a");
          a.href = url;
          a.download = "polaris-alerts.csv";
          a.click();
          URL.revokeObjectURL(url);
        }}
      >
        Export CSV
      </button>
      {DEMO.map((d) => (
        <button
          key={d.tier}
          type="button"
          className="hud-panel px-2 py-1 text-[10px] font-bold uppercase"
          onClick={() => pushAlert(d.tier, d.message)}
        >
          {d.tier}
        </button>
      ))}
    </div>
  );
}
