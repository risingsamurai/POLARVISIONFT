import { create } from "zustand";
import {
  ALL_ICEBERGS,
  MOCK_ROUTES,
  MOCK_VESSEL,
  type Iceberg,
  type RouteOption,
  type VesselState,
} from "./mockData";

export type DataStatus = "LIVE" | "FALLBACK";

export interface DataSourceReality {
  status: DataStatus;
  lastLive: string | null;
  reason: string | null;
}

export interface Layers {
  seaIce: boolean;
  icebergs: boolean;
  predictions: boolean;
  riskZones: boolean;
  route: boolean;
  vessel: boolean;
}

export interface KeysDown {
  w: boolean;
  a: boolean;
  s: boolean;
  d: boolean;
  up: boolean;
  down: boolean;
  left: boolean;
  right: boolean;
}

interface PolarisState {
  vessel: VesselState;
  icebergs: Iceberg[];
  selectedIcebergId: string | null;
  routes: RouteOption[];
  lockedRouteId: RouteOption["id"];
  routeVersion: number;
  layers: Layers;
  keys: KeysDown;
  cameraOrbiting: boolean;
  cameraDistance: number;
  orbitYaw: number;
  orbitPitch: number;
  simTimeIso: string;
  dataReality: {
    nsidc: DataSourceReality;
    byu: DataSourceReality;
    era5: DataSourceReality;
  };
  setVessel: (partial: Partial<VesselState>) => void;
  selectIceberg: (id: string | null) => void;
  toggleLayer: (key: keyof Layers) => void;
  setKey: (key: keyof KeysDown, down: boolean) => void;
  setCameraOrbiting: (v: boolean) => void;
  setOrbit: (yaw: number, pitch: number, distance?: number) => void;
  recalculateRoute: () => void;
  lockRoute: (id: RouteOption["id"]) => void;
  tickTime: () => void;
  autoMode: boolean;
  forecastDay: number;
  destination: { lat: number; lon: number };
  iceGrid: { lat: number; lon: number; sic: number }[];
  alerts: { id?: string; tier: string; message: string; ts: string; timestamp?: string }[];
  detections: {
    name: string;
    confidence: number;
    distanceNm: number;
    lat: number;
    lon: number;
  }[];
  setIceGrid: (grid: { lat: number; lon: number; sic: number }[]) => void;
  setIcebergs: (icebergs: Iceberg[]) => void;
  setRoutes: (routes: RouteOption[]) => void;
  setAutoMode: (v: boolean) => void;
  setForecastDay: (d: number) => void;
  setDestination: (d: { lat: number; lon: number }) => void;
  soundOn: boolean;
  setSoundOn: (v: boolean) => void;
  pushAlert: (tier: string, message: string) => void;
  pushDetection: (d: PolarisState["detections"][number]) => void;
  setDataReality: (dataReality: PolarisState["dataReality"]) => void;
}

const fallback = (reason: string): DataSourceReality => ({
  status: "FALLBACK",
  lastLive: null,
  reason,
});

export const usePolarisStore = create<PolarisState>((set, get) => ({
  vessel: { ...MOCK_VESSEL },
  icebergs: [],
  selectedIcebergId: null,
  routes: MOCK_ROUTES,
  lockedRouteId: "balanced",
  routeVersion: 0,
  layers: {
    seaIce: true,
    icebergs: true,
    predictions: true,
    riskZones: true,
    route: true,
    vessel: true,
  },
  keys: {
    w: false,
    a: false,
    s: false,
    d: false,
    up: false,
    down: false,
    left: false,
    right: false,
  },
  cameraOrbiting: false,
  cameraDistance: 38,
  orbitYaw: 0,
  orbitPitch: 0.42,
  simTimeIso: new Date().toISOString(),
  dataReality: {
    nsidc: fallback("Phase 1 mock ice grid; NSIDC fetcher not wired"),
    byu: fallback("Phase 1 mock icebergs; BYU scrape is Phase 2"),
    era5: fallback("Phase 1 unused; no CDS key"),
  },
  setVessel: (partial) =>
    set((s) => ({ vessel: { ...s.vessel, ...partial } })),
  selectIceberg: (id) => set({ selectedIcebergId: id }),
  toggleLayer: (key) =>
    set((s) => ({ layers: { ...s.layers, [key]: !s.layers[key] } })),
  setKey: (key, down) => set((s) => ({ keys: { ...s.keys, [key]: down } })),
  setCameraOrbiting: (v) => set({ cameraOrbiting: v }),
  setOrbit: (yaw, pitch, distance) =>
    set((s) => ({
      orbitYaw: yaw,
      orbitPitch: pitch,
      cameraDistance: distance ?? s.cameraDistance,
    })),
  lockRoute: (id) => set({ lockedRouteId: id }),
  recalculateRoute: async () => {
    const { vessel, destination, routeVersion } = get();
    try {
      const { fetchRoutes } = await import("./api");
      const data = await fetchRoutes([vessel.lat, vessel.lon], [destination.lat, destination.lon]);
      if (data.routes && data.routes.length > 0) {
        set({
          routes: data.routes,
          routeVersion: routeVersion + 1,
          alerts: [
            ...get().alerts.slice(-40),
            {
              id: `INFO-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
              tier: "INFO",
              message: "A* land-avoiding route recalculating via backend",
              ts: new Date().toISOString(),
              timestamp: new Date().toISOString(),
            },
          ],
        });
      }
    } catch (err) {
      console.error("Failed to recalculate route:", err);
    }
  },
  tickTime: () => set({ simTimeIso: new Date().toISOString() }),
  autoMode: false,
  forecastDay: 3,
  destination: { lat: -68.72, lon: -49.55 },
  iceGrid: [],
  alerts: [],
  detections: [],
  soundOn: false,
  setIceGrid: (iceGrid) => set({ iceGrid }),
  setIcebergs: (icebergs) => set({ icebergs }),
  setRoutes: (routes) => set({ routes }),
  setAutoMode: (v) => set({ autoMode: v }),
  setSoundOn: (v) => set({ soundOn: v }),
  setForecastDay: (d) => set({ forecastDay: d }),
  setDestination: (d) => set({ destination: d }),
  pushAlert: (tier, message) =>
    set((s) => {
      const ts = new Date().toISOString();
      const id = `${tier}-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
      return {
        alerts: [
          ...s.alerts.slice(-40),
          { id, tier, message, ts, timestamp: ts },
        ],
      };
    }),
  pushDetection: (d) =>
    set((s) => ({ detections: [...s.detections.slice(-30), d] })),
  setDataReality: (dataReality) => set({ dataReality }),
}));

export const selectLockedRoute = (s: PolarisState) =>
  s.routes.find((r) => r.id === s.lockedRouteId) ?? s.routes[0];
