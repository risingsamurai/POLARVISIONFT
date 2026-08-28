/** Local tangent-plane projection around the Weddell Sea origin. 1 scene unit ≈ 1 nm. */

import { SCENE_ORIGIN } from "./mockData";

const NM_PER_DEG_LAT = 60;

export function latLonToScene(
  lat: number,
  lon: number,
  origin = SCENE_ORIGIN
): [number, number, number] {
  const x =
    (lon - origin.lon) *
    NM_PER_DEG_LAT *
    Math.cos((origin.lat * Math.PI) / 180);
  const z = -(lat - origin.lat) * NM_PER_DEG_LAT;
  return [x, 0, z];
}

export function sceneToLatLon(
  x: number,
  z: number,
  origin = SCENE_ORIGIN
): { lat: number; lon: number } {
  const lat = origin.lat - z / NM_PER_DEG_LAT;
  const lon =
    origin.lon +
    x / (NM_PER_DEG_LAT * Math.cos((origin.lat * Math.PI) / 180));
  return { lat, lon };
}

export function haversineNm(
  a: { lat: number; lon: number },
  b: { lat: number; lon: number }
): number {
  const R = 3440.065;
  const dLat = ((b.lat - a.lat) * Math.PI) / 180;
  const dLon = ((b.lon - a.lon) * Math.PI) / 180;
  const la1 = (a.lat * Math.PI) / 180;
  const la2 = (b.lat * Math.PI) / 180;
  const h =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(la1) * Math.cos(la2) * Math.sin(dLon / 2) ** 2;
  return 2 * R * Math.asin(Math.min(1, Math.sqrt(h)));
}

export function headingToVector(headingDeg: number): [number, number] {
  const rad = ((90 - headingDeg) * Math.PI) / 180;
  return [Math.cos(rad), -Math.sin(rad)];
}
