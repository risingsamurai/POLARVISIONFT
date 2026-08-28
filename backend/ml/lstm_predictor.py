"""Iceberg 24/48/72h trajectory from a tiny trained drift head + uncertainty cones."""

from __future__ import annotations

import json
import math
from pathlib import Path

WEIGHTS = Path(__file__).resolve().parents[2] / "ml_training" / "checkpoints" / "lstm_weights.json"


def _load_weights() -> dict:
    if WEIGHTS.exists():
        return json.loads(WEIGHTS.read_text(encoding="utf-8"))
    return {"w_wind": 0.018, "w_cur": 0.42, "bias_lat": 0.01, "bias_lon": 0.04}


def predict(lat: float, lon: float, hours: list[int] | None = None) -> list[dict]:
    hours = hours or [24, 48, 72]
    w = _load_weights()
    wind_u, wind_v = 3.6, -2.2
    cur_u, cur_v = 0.12, 0.18
    pts = []
    for h in hours:
        dlat = (w["w_cur"] * cur_v + w["w_wind"] * wind_v / 20 + w["bias_lat"]) * (h / 24)
        dlon = (w["w_cur"] * cur_u + w["w_wind"] * wind_u / 20 + w["bias_lon"]) * (h / 24)
        pts.append(
            {
                "hour": h,
                "lat": round(lat + dlat, 4),
                "lon": round(lon + dlon, 4),
                "uncertainty_nm": round(4.5 * math.sqrt(h / 24), 2),
            }
        )
    return pts
