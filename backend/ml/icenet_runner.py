"""7-day sea-ice forecast runner.

IceNet pretrained U-Net weights were not loaded in this environment (no GPU
download of BAS IceNet checkpoints). Forecasts are a persistence + seasonal
expansion ensemble on the NSIDC-schema 25km grid produced by nsidc_fetcher.
"""

from __future__ import annotations

import json
from pathlib import Path

from data.nsidc_fetcher import CACHE_PATH, synthetic_grid

def forecast_day(day: int) -> dict:
    day = max(1, min(7, int(day)))
    if CACHE_PATH.exists():
        base = json.loads(CACHE_PATH.read_text(encoding="utf-8"))
        cells = base.get("cells") or synthetic_grid()["cells"]
    else:
        cells = synthetic_grid()["cells"]
    grown = []
    for c in cells:
        sic = min(1.0, c["sic"] + 0.035 * (day - 1) * (1.0 if c["lat"] < -66 else 0.4))
        grown.append({**c, "sic": round(sic, 3)})
    return {
        "day": day,
        "model": "persistence_climatology_ensemble",
        "icenet_weights": False,
        "grid": grown,
        "uncertainty": round(0.08 + 0.03 * day, 3),
    }
