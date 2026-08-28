"""Evaluate 24/48/72h mean positional error (nautical miles) on holdout tracks."""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT / "ml_training"))

from data.byu_scraper import run as scrape_byu  # noqa: E402
from train_lstm import simulate_track  # noqa: E402

CKPT = Path(__file__).parent / "checkpoints" / "lstm_weights.json"


def haversine_nm(lat1, lon1, lat2, lon2) -> float:
    r = 3440.065
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    la1, la2 = math.radians(lat1), math.radians(lat2)
    h = math.sin(dlat / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin(dlon / 2) ** 2
    return 2 * r * math.asin(min(1.0, math.sqrt(h)))


def predict_step(lat, lon, w, hours: int):
    wind_u, wind_v, cur_u, cur_v = 3.6, -2.2, 0.12, 0.18
    dlat = (w["w_cur"] * cur_v + w["w_wind"] * wind_v / 20 + w["bias_lat"]) * (hours / 24)
    dlon = (w["w_cur"] * cur_u + w["w_wind"] * wind_u / 20 + w["bias_lon"]) * (hours / 24)
    return lat + dlat, lon + dlon


def main() -> None:
    if not CKPT.exists():
        from train_lstm import train

        train()
    w = json.loads(CKPT.read_text(encoding="utf-8"))
    bergs = scrape_byu()["icebergs"]
    errors = {24: [], 48: [], 72: []}
    for i, b in enumerate(bergs):
        track = simulate_track(b["lat"], b["lon"], 21, seed=1000 + i)
        origin = track[0]
        for h, idx in ((24, 1), (48, 2), (72, 3)):
            plat, plon = predict_step(origin[0], origin[1], w, h)
            errors[h].append(haversine_nm(plat, plon, track[idx][0], track[idx][1]))
    summary = {
        "n_icebergs": len(bergs),
        "mean_error_nm": {str(h): round(float(np.mean(errors[h])), 2) for h in errors},
        "median_error_nm": {str(h): round(float(np.median(errors[h])), 2) for h in errors},
    }
    out = Path(__file__).parent / "checkpoints" / "eval_metrics.json"
    out.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
