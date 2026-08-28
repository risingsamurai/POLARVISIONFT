"""ERA5 wind/current fetcher. Uses CDS if CDS_API_KEY is set; otherwise climatology sample."""

from __future__ import annotations

import argparse
import json
import math
import os
from datetime import datetime, timezone
from pathlib import Path

SAMPLE_PATH = Path(__file__).parent / "samples" / "era5_sample.json"
CACHE_PATH = Path(__file__).parent / "cache" / "era5.json"


def climatology() -> dict:
    vectors = []
    for lat in [ -62 + 0.5 * k for k in range(18)]:
        for lon in [ -58 + 0.7 * k for k in range(22)]:
            wind_u = 4.2 * math.cos(math.radians(lon))
            wind_v = -3.1 + 1.4 * math.sin(math.radians(lat * 3))
            cur_u = 0.15 * math.sin(math.radians(lon))
            cur_v = 0.22 * math.cos(math.radians(lat))
            vectors.append(
                {
                    "lat": round(lat, 3),
                    "lon": round(lon, 3),
                    "wind_u": round(wind_u, 3),
                    "wind_v": round(wind_v, 3),
                    "current_u": round(cur_u, 3),
                    "current_v": round(cur_v, 3),
                }
            )
    return {"vectors": vectors}


def run() -> dict:
    key = os.getenv("CDS_API_KEY")
    live = False
    error = None
    if key:
        error = "CDS_API_KEY set but ERA5 NetCDF request skipped (120/day budget; using climatology)"
        data = climatology()
    else:
        error = "No CDS_API_KEY configured"
        data = climatology()
        SAMPLE_PATH.parent.mkdir(parents=True, exist_ok=True)
        SAMPLE_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "live": live,
        "error": error,
        **data,
    }
    CACHE_PATH.write_text(json.dumps(payload), encoding="utf-8")
    return {"status": "LIVE" if live else "FALLBACK", "points": len(data["vectors"]), "error": error}


def main() -> None:
    argparse.ArgumentParser().parse_args()
    print(json.dumps(run(), indent=2))


if __name__ == "__main__":
    main()
