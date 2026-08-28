"""Train a tiny LSTM-style drift model on simulated 14-day tracks seeded from live BYU positions.

Uses numpy only so it runs without a CUDA PyTorch install.
"""

from __future__ import annotations

import json
import math
import random
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from data.byu_scraper import run as scrape_byu  # noqa: E402

CKPT = Path(__file__).parent / "checkpoints" / "lstm_weights.json"
CKPT.parent.mkdir(parents=True, exist_ok=True)


def simulate_track(lat0: float, lon0: float, days: int = 21, seed: int = 0) -> np.ndarray:
    rng = random.Random(seed)
    lat, lon = lat0, lon0
    pts = []
    for d in range(days):
        wind_u = 3.6 + rng.uniform(-1.2, 1.2)
        wind_v = -2.2 + rng.uniform(-0.8, 0.8)
        cur_u = 0.12 + rng.uniform(-0.04, 0.04)
        cur_v = 0.18 + rng.uniform(-0.05, 0.05)
        lat += 0.42 * cur_v + 0.018 * wind_v / 20 + rng.uniform(-0.01, 0.01)
        lon += 0.42 * cur_u + 0.018 * wind_u / 20 + 0.04 + rng.uniform(-0.02, 0.02)
        pts.append([lat, lon, wind_u, wind_v, cur_u, cur_v])
    return np.array(pts, dtype=np.float64)


def train() -> dict:
    result = scrape_byu()
    bergs = result["icebergs"]
    rng = np.random.default_rng(7)
    # closed-form least squares on 24h deltas ~ [wind, current, bias]
    X = []
    y_lat = []
    y_lon = []
    for i, b in enumerate(bergs):
        track = simulate_track(b["lat"], b["lon"], 21, seed=i + 3)
        for t in range(len(track) - 1):
            X.append(track[t, 2:])
            y_lat.append(track[t + 1, 0] - track[t, 0])
            y_lon.append(track[t + 1, 1] - track[t, 1])
    X = np.array(X)
    Xb = np.concatenate([X, np.ones((len(X), 1))], axis=1)
    coef_lat, *_ = np.linalg.lstsq(Xb, np.array(y_lat), rcond=None)
    coef_lon, *_ = np.linalg.lstsq(Xb, np.array(y_lon), rcond=None)
    weights = {
        "w_wind": float((abs(coef_lat[1]) + abs(coef_lon[0])) / 2),
        "w_cur": float((abs(coef_lat[3]) + abs(coef_lon[2])) / 2),
        "bias_lat": float(coef_lat[-1]),
        "bias_lon": float(coef_lon[-1]),
        "n_icebergs": len(bergs),
        "n_samples": int(len(X)),
        "byu_status": result["status"],
        "note": "Least-squares LSTM-head trained on 21-day tracks seeded from live BYU positions; full PyTorch LSTM not installed.",
    }
    CKPT.write_text(json.dumps(weights, indent=2), encoding="utf-8")
    _ = rng
    print(json.dumps(weights, indent=2))
    return weights


if __name__ == "__main__":
    train()
