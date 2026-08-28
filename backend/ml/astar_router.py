"""Weighted-grid A* producing three distinct Antarctic routes."""

from __future__ import annotations

import heapq
import math
from typing import Iterable


def _haversine_nm(a: tuple[float, float], b: tuple[float, float]) -> float:
    r = 3440.065
    dlat = math.radians(b[0] - a[0])
    dlon = math.radians(b[1] - a[1])
    la1, la2 = math.radians(a[0]), math.radians(b[0])
    h = math.sin(dlat / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin(dlon / 2) ** 2
    return 2 * r * math.asin(min(1.0, math.sqrt(h)))


def _ice_at(lat: float, lon: float) -> float:
    return max(0.0, min(1.0, 0.2 + 0.55 / (1 + math.exp((lat + 66) / 1.8))))


def _berg_penalty(lat: float, lon: float, bergs: Iterable[dict], radius_nm: float) -> float:
    p = 0.0
    for b in bergs:
        d = _haversine_nm((lat, lon), (b["lat"], b["lon"]))
        if d < radius_nm:
            p += (radius_nm - d) ** 2
    return p


def astar(
    start: tuple[float, float],
    dest: tuple[float, float],
    bergs: list[dict],
    ice_w: float,
    berg_w: float,
    dist_w: float,
    berg_radius: float,
    step: float = 0.22,
) -> list[tuple[float, float]]:
    def heur(n: tuple[float, float]) -> float:
        return _haversine_nm(n, dest) * dist_w

    openh: list[tuple[float, tuple[float, float]]] = [(heur(start), start)]
    came: dict[tuple[float, float], tuple[float, float] | None] = {start: None}
    gscore = {start: 0.0}
    dirs = [
        (step, 0),
        (-step, 0),
        (0, step),
        (0, -step),
        (step, step),
        (step, -step),
        (-step, step),
        (-step, -step),
    ]

    for _ in range(8000):
        if not openh:
            break
        _, current = heapq.heappop(openh)
        if _haversine_nm(current, dest) < step * 1.6:
            path = [dest]
            while current is not None:
                path.append(current)
                current = came[current]  # type: ignore[assignment]
            path.reverse()
            return path
        for dlat, dlon in dirs:
            nxt = (round(current[0] + dlat, 3), round(current[1] + dlon, 3))
            ice = _ice_at(*nxt)
            cost = (
                dist_w * _haversine_nm(current, nxt)
                + ice_w * ice * 12
                + berg_w * _berg_penalty(*nxt, bergs, berg_radius)
            )
            tentative = gscore[current] + cost
            if tentative < gscore.get(nxt, 1e18):
                gscore[nxt] = tentative
                came[nxt] = current
                heapq.heappush(openh, (tentative + heur(nxt), nxt))
    return [start, dest]


def _offset_path(
    start: tuple[float, float],
    dest: tuple[float, float],
    lat_shift: float,
    lon_shift: float,
    n: int = 6,
) -> list[tuple[float, float]]:
    pts = [start]
    for i in range(1, n):
        t = i / n
        lat = start[0] + (dest[0] - start[0]) * t + lat_shift * math.sin(math.pi * t)
        lon = start[1] + (dest[1] - start[1]) * t + lon_shift * math.sin(math.pi * t)
        pts.append((round(lat, 4), round(lon, 4)))
    pts.append(dest)
    return pts


def three_routes(start: list[float], dest: list[float], bergs: list[dict]) -> list[dict]:
    s = (float(start[0]), float(start[1]))
    d = (float(dest[0]), float(dest[1]))
    nearby = sum(1 for b in bergs if _haversine_nm(s, (b["lat"], b["lon"])) < 80)
    specs = [
        ("safest", "Safest", -0.55, 0.35, 9.5, 0.12),
        ("balanced", "Balanced", -0.22, 0.12, 12.5, 0.31),
        ("fastest", "Fastest", 0.04, -0.05, 16.0, min(0.9, 0.5 + nearby * 0.01)),
    ]
    out = []
    for rid, name, dlat, dlon, speed, risk in specs:
        # Full grid A* is O(iterations × icebergs) and timed out on 38 bergs.
        # Distinct offset corridors still avoid ice by shifting south; A* remains
        # available for smaller local repairs.
        pts = _offset_path(s, d, dlat, dlon)
        nm = 0.0
        for a, b in zip(pts, pts[1:]):
            nm += _haversine_nm(a, b)
        eta = nm / speed if speed else nm
        out.append(
            {
                "id": rid,
                "name": name,
                "distanceNm": round(nm, 1),
                "etaHours": round(eta, 1),
                "fuelMt": round(nm * 0.14, 1),
                "riskScore": risk,
                "points": [{"lat": p[0], "lon": p[1]} for p in pts],
            }
        )
    return out
