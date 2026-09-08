"use client";

import dynamic from "next/dynamic";
import { useEffect } from "react";
import Link from "next/link";
import { AlertBanner } from "@/components/HUD/AlertBanner";
import { AutoControls } from "@/components/HUD/AutoControls";
import { DataRealityBadge } from "@/components/HUD/DataRealityBadge";
import { DetectionLog } from "@/components/HUD/DetectionLog";
import { AlertHistoryLog } from "@/components/HUD/AlertHistoryLog";
import { ExportPdfButton } from "@/components/HUD/ExportPdfButton";
import { ForecastSlider } from "@/components/HUD/ForecastSlider";
import { IcebergInfoPanel } from "@/components/HUD/IcebergInfoPanel";
import { IceLevelLegend } from "@/components/HUD/IceLevelLegend";
import { LayerControlPanel } from "@/components/HUD/LayerControlPanel";
import { Minimap } from "@/components/HUD/Minimap";
import { MovementControls } from "@/components/HUD/MovementControls";
import { RouteInfoPanel } from "@/components/HUD/RouteInfoPanel";
import { TopBar } from "@/components/HUD/TopBar";
import { fetchIcebergs, fetchRoutes } from "@/lib/api";
import { ALL_ICEBERGS } from "@/lib/mockData";
import { usePolarisStore, type KeysDown } from "@/lib/store";

const SceneCanvas = dynamic(
  () => import("@/components/Scene/SceneCanvas").then((m) => m.SceneCanvas),
  { ssr: false }
);

const KEY_MAP: Record<string, keyof KeysDown> = {
  KeyW: "w",
  w: "w",
  W: "w",
  KeyA: "a",
  a: "a",
  A: "a",
  KeyS: "s",
  s: "s",
  S: "s",
  KeyD: "d",
  d: "d",
  D: "d",
  ArrowUp: "up",
  ArrowDown: "down",
  ArrowLeft: "left",
  ArrowRight: "right",
};

export default function SimulationPage() {
  const setKey = usePolarisStore((s) => s.setKey);
  const setIcebergs = usePolarisStore((s) => s.setIcebergs);
  const setRoutes = usePolarisStore((s) => s.setRoutes);
  const setDataReality = usePolarisStore((s) => s.setDataReality);
  const pushDetection = usePolarisStore((s) => s.pushDetection);

  useEffect(() => {
    const down = (e: KeyboardEvent) => {
      const k = KEY_MAP[e.code] || KEY_MAP[e.key];
      if (!k) return;
      e.preventDefault();
      setKey(k, true);
    };
    const up = (e: KeyboardEvent) => {
      const k = KEY_MAP[e.code] || KEY_MAP[e.key];
      if (!k) return;
      setKey(k, false);
    };
    window.addEventListener("keydown", down);
    window.addEventListener("keyup", up);

    // Fetch initial backend A* routes
    const { vessel, destination } = usePolarisStore.getState();
    fetchRoutes([vessel.lat, vessel.lon], [destination.lat, destination.lon])
      .then((data) => {
        if (data.routes?.length) {
          setRoutes(data.routes);
        }
      })
      .catch((err) => console.error("Initial 3D route fetch failed:", err));

    fetchIcebergs()
      .then((data) => {
        if (data.icebergs?.length) {
          const processedIcebergs = data.icebergs.map((ib) => ({
            ...ib,
            headingDeg: ib.headingDeg ?? 90,
            predictedPath: ib.predictedPath ?? [],
          }));
          setIcebergs(processedIcebergs);
          
          const API = process.env.NEXT_PUBLIC_API_URL ?? "";
          fetch(`${API}/api/status`)
            .then((res) => {
              if (!res.ok) throw new Error("status fetch failed");
              return res.json();
            })
            .then((data) => {
              setDataReality({
                nsidc: {
                  status: data.nsidc?.status ?? "FALLBACK",
                  lastLive: data.nsidc?.fetched_at ?? null,
                  reason: data.nsidc?.status === "FALLBACK" ? (data.nsidc?.error ?? "Unknown error") : null,
                },
                byu: {
                  status: data.byu?.status ?? "FALLBACK",
                  lastLive: data.byu?.status === "LIVE" ? new Date().toISOString() : null,
                  reason: data.byu?.status === "FALLBACK" ? (data.byu?.error ?? "Unknown error") : null,
                },
                era5: {
                  status: data.era5?.status ?? "FALLBACK",
                  lastLive: data.era5?.fetched_at ?? null,
                  reason: data.era5?.status === "FALLBACK" ? (data.era5?.error ?? "Unknown error") : null,
                },
              });
            })
            .catch((err) => console.error("Error fetching status in simulation:", err));
        } else {
          setIcebergs(ALL_ICEBERGS);
        }
      })
      .catch(() => {
        setIcebergs(ALL_ICEBERGS);
      });

    const API = process.env.NEXT_PUBLIC_API_URL ?? "";
    fetch(`${API}/api/ice/current`)
      .then((res) => {
        if (!res.ok) throw new Error("current ice fetch failed");
        return res.json();
      })
      .then((data) => {
        if (data.grid) {
          usePolarisStore.getState().setIceGrid(data.grid);
        }
      })
      .catch(() => undefined);

    return () => {
      window.removeEventListener("keydown", down);
      window.removeEventListener("keyup", up);
    };
  }, [setKey, setIcebergs, setRoutes, setDataReality, pushDetection]);

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
        <div className="flex-1 flex justify-between items-start pointer-events-none">
          <div className="pointer-events-none flex flex-col gap-2">
            <div className="pointer-events-auto">
              <LayerControlPanel />
            </div>
            <div className="pointer-events-auto">
              <IceLevelLegend />
            </div>
            <div className="pointer-events-auto">
              <ForecastSlider />
            </div>
            <div className="pointer-events-auto">
              <DataRealityBadge />
            </div>
            <div className="pointer-events-auto">
              <Link href="/" className="hud-panel inline-block px-3 py-2 text-[10px] uppercase tracking-wide">
                Overview map
              </Link>
            </div>
          </div>
          <div className="pointer-events-none flex flex-col gap-2">
            <div className="pointer-events-auto">
              <IcebergInfoPanel />
            </div>
            <div className="pointer-events-auto">
              <RouteInfoPanel />
            </div>
            <div className="pointer-events-auto">
              <AutoControls />
            </div>
            <div className="pointer-events-auto">
              <DetectionLog />
            </div>
            <div className="pointer-events-auto">
              <AlertHistoryLog />
            </div>
            <div className="pointer-events-auto">
              <ExportPdfButton />
            </div>
          </div>
        </div>
        <div className="flex items-end justify-between pointer-events-none">
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
