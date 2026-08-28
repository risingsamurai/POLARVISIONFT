"""NSIDC sea-ice concentration fetcher. Falls back to a generated 25km-style grid."""

from __future__ import annotations

import argparse
import json
import math
import os
from datetime import datetime, timezone
from pathlib import Path

SAMPLE_PATH = Path(__file__).parent / "samples" / "nsidc_sic_sample.json"
CACHE_PATH = Path(__file__).parent / "cache" / "nsidc_sic.json"


def synthetic_grid(day_offset: int = 0) -> dict:
    """25km-ish polar stereographic-style lat/lon cells over Weddell Sea."""
    cells = []
    for i, lat in enumerate([ -62 + 0.4 * k for k in range(22)]):
        for j, lon in enumerate([ -60 + 0.6 * k for k in range(28)]):
            ice = 0.15 + 0.55 * (1 / (1 + math.exp((lat + 66) / 1.8)))
            ice += 0.08 * math.sin((lon + 50) / 8 + day_offset / 3)
            ice = max(0.0, min(1.0, ice))
            cells.append({"lat": round(lat, 3), "lon": round(lon, 3), "sic": round(ice, 3)})
    return {
        "grid_km": 25,
        "day_offset": day_offset,
        "cells": cells,
    }


def run() -> dict:
    user = os.getenv("EARTHDATA_USERNAME")
    password = os.getenv("EARTHDATA_PASSWORD")
    live = False
    error = None
    if user and password:
        error = "Earthdata credentials present but NSIDC NetCDF download not executed in this build"
        grid = synthetic_grid()
    else:
        error = "No Earthdata account configured"
        grid = synthetic_grid()
        if SAMPLE_PATH.exists():
            grid = json.loads(SAMPLE_PATH.read_text(encoding="utf-8"))
        else:
            SAMPLE_PATH.parent.mkdir(parents=True, exist_ok=True)
            SAMPLE_PATH.write_text(json.dumps(grid, indent=2), encoding="utf-8")
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "live": live,
        "error": error,
        **grid,
    }
    CACHE_PATH.write_text(json.dumps(payload), encoding="utf-8")
    return {"status": "LIVE" if live else "FALLBACK", "cells": len(grid["cells"]), "error": error}


def main() -> None:
    argparse.ArgumentParser().parse_args()
    print(json.dumps(run(), indent=2))


if __name__ == "__main__":
    main()
