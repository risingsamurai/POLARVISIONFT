"use client";

import dynamic from "next/dynamic";
import { useEffect } from "react";
import Link from "next/link";
import { AlertBanner } from "@/components/HUD/AlertBanner";
import { AutoControls } from "@/components/HUD/AutoControls";
import { DataRealityBadge } from "@/components/HUD/DataRealityBadge";
import { DetectionLog } from "@/components/HUD/DetectionLog";
import { ExportPdfButton } from "@/components/HUD/ExportPdfButton";
import { ForecastSlider } from "@/components/HUD/ForecastSlider";
import { IcebergInfoPanel } from "@/components/HUD/IcebergInfoPanel";
import { IceLevelLegend } from "@/components/HUD/IceLevelLegend";
import { LayerControlPanel } from "@/components/HUD/LayerControlPanel";
import { Minimap } from "@/components/HUD/Minimap";
import { MovementControls } from "@/components/HUD/MovementControls";
import { RouteInfoPanel } from "@/components/HUD/RouteInfoPanel";
import { TopBar } from "@/components/HUD/TopBar";
import { fetchIcebergs } from "@/lib/api";
import { usePolarisStore, type KeysDown } from "@/lib/store";

const SceneCanvas = dynamic(
  () => import("@/components/Scene/SceneCanvas").then((m) => m.SceneCanvas),
  { ssr: false }
);

const KEY_MAP: Record<string, keyof KeysDown> = {
  KeyW: "w",
  KeyA: "a",
  KeyS: "s",
  KeyD: "d",
  ArrowUp: "up",
  ArrowDown: "down",
  ArrowLeft: "left",
  ArrowRight: "right",
};

export default function SimulationPage() {
  const setKey = usePolarisStore((s) => s.setKey);
  const setIcebergs = usePolarisStore((s) => s.setIcebergs);
  const setDataReality = usePolarisStore((s) => s.setDataReality);
  const pushDetection = usePolarisStore((s) => s.pushDetection);

  useEffect(() => {
    const down = (e: KeyboardEvent) => {
      const k = KEY_MAP[e.code];
      if (!k) return;
      e.preventDefault();
      setKey(k, true);
    };
    const up = (e: KeyboardEvent) => {
      const k = KEY_MAP[e.code];
      if (!k) return;
      setKey(k, false);
    };
    window.addEventListener("keydown", down);
    window.addEventListener("keyup", up);
    fetchIcebergs()
      .then((data) => {
        if (data.icebergs?.length) {
          const withDebris = [
            ...data.icebergs.map((ib) => ({
              ...ib,
              headingDeg: ib.headingDeg ?? 90,
              predictedPath: ib.predictedPath ?? [],
            })),
            {
              id: "DEB-GHOSTNET-01",
              name: "GHOST-NET",
              lat: -68.33,
              lon: -52.2,
              diameterNm: 0.2,
              sizeClass: "small" as const,
              status: "tracked" as const,
              highRisk: true,
              dangerRadiusNm: 4,
              headingDeg: 0,
              predictedPath: [],
            },
          ];
          setIcebergs(withDebris);
          pushDetection({
            name: "GHOST-NET",
            confidence: 0.91,
            distanceNm: 6.2,
            lat: -68.33,
            lon: -52.2,
          });
          setDataReality({
            nsidc: {
              status: "FALLBACK",
              lastLive: null,
              reason: "No Earthdata account",
            },
            byu: {
              status: "LIVE",
              lastLive: new Date().toISOString(),
              reason: null,
            },
            era5: {
              status: "FALLBACK",
              lastLive: null,
              reason: "No CDS key",
            },
          });
        }
      })
      .catch(() => undefined);
    return () => {
      window.removeEventListener("keydown", down);
      window.removeEventListener("keyup", up);
    };
  }, [setKey, setIcebergs, setDataReality, pushDetection]);

  return (
    <main className="relative h-screen w-screen overflow-hidden bg-slate-900">
      <div className="absolute inset-0">
        <SceneCanvas />
      </div>
      <div className="pointer-events-none absolute inset-0 p-3 flex flex-col gap-3">
        <div className="pointer-events-auto space-y-2">
          <TopBar />
          <AlertBanner />
        </div>
        <div className="flex-1 flex justify-between items-start">
          <div className="pointer-events-auto flex flex-col gap-2">
            <LayerControlPanel />
            <IceLevelLegend />
            <ForecastSlider />
            <DataRealityBadge />
            <Link href="/" className="hud-panel px-3 py-2 text-[10px] uppercase tracking-wide">
              Overview map
            </Link>
          </div>
          <div className="pointer-events-auto flex flex-col gap-2">
            <IcebergInfoPanel />
            <RouteInfoPanel />
            <AutoControls />
            <DetectionLog />
            <ExportPdfButton />
          </div>
        </div>
        <div className="flex items-end justify-between">
          <div className="pointer-events-auto">
            <Minimap />
          </div>
          <div className="pointer-events-auto mx-auto mb-1">
            <MovementControls />
          </div>
          <div className="w-[200px]" />
        </div>
      </div>
    </main>
  );
}
