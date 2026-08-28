"use client";

import { usePolarisStore } from "@/lib/store";

function KeyCap({
  label,
  active,
}: {
  label: string;
  active: boolean;
}) {
  return (
    <span
      className={`grid h-8 w-8 place-items-center rounded-lg border text-xs font-bold font-mono transition-all duration-100 ${
        active
          ? "bg-cyan-500 border-cyan-400 text-white shadow-lg shadow-cyan-500/40 scale-95"
          : "bg-white/10 border-white/15 text-white/80"
      }`}
    >
      {label}
    </span>
  );
}

export function MovementControls() {
  const keys = usePolarisStore((s) => s.keys);
  const orbiting = usePolarisStore((s) => s.cameraOrbiting);

  return (
    <section className="hud-panel px-5 py-3 flex items-center gap-6 bg-black/40 backdrop-blur-md border border-white/10 rounded-xl text-white shadow-xl">
      <div>
        <h2 className="hud-header mb-2 text-center text-[10px] font-bold uppercase tracking-[0.18em] text-white/50">
          Manual Helm
        </h2>
        <div className="grid grid-cols-3 gap-1.5 w-[112px]">
          <span />
          <KeyCap label="W" active={keys.w || keys.up} />
          <span />
          <KeyCap label="A" active={keys.a || keys.left} />
          <KeyCap label="S" active={keys.s || keys.down} />
          <KeyCap label="D" active={keys.d || keys.right} />
        </div>
      </div>
      <div className="h-12 w-[1px] bg-white/10" />
      <div className="text-center">
        <h2 className="hud-header mb-2 text-[10px] font-bold uppercase tracking-[0.18em] text-white/50">
          Camera
        </h2>
        <div
          className={`h-14 w-14 rounded-full border-2 grid place-items-center text-[10px] font-bold uppercase tracking-wider transition-all duration-200 ${
            orbiting
              ? "border-cyan-400 bg-cyan-500/30 text-cyan-200 shadow-md shadow-cyan-500/30 scale-105"
              : "border-white/20 bg-white/5 text-white/70 hover:border-white/40"
          }`}
        >
          {orbiting ? "Orbiting" : "Drag"}
        </div>
      </div>
    </section>
  );
}

