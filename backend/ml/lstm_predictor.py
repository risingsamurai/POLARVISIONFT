"""Iceberg 24/48/72h trajectory predictions using a trained PyTorch LSTM.

Reconstructs the past 14 days of history using SQLite database logs,
falling back to physics-informed backward simulation if history is incomplete.
"""

from __future__ import annotations

import math
import os
import sqlite3
from pathlib import Path
import numpy as np
import xarray as xr
import torch
import torch.nn as nn

# Paths
ROOT = Path(__file__).resolve().parents[2]
MODEL_PATH = Path(__file__).resolve().parent / "lstm_weights.pt"
ERA5_CACHE = ROOT / "backend" / "data" / "cache" / "era5_latest.nc"
DB_PATH = ROOT / "backend" / "polaris.db"


class IcebergLSTM(nn.Module):
    def __init__(self, input_size=6, hidden_size=32, num_layers=1, output_size=6):
        super().__init__()
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True)
        self.fc = nn.Linear(hidden_size, output_size)
        
    def forward(self, x):
        out, _ = self.lstm(x)
        last_out = out[:, -1, :]
        preds = self.fc(last_out)
        return preds


_model = None


def get_model():
    global _model
    if _model is None:
        _model = IcebergLSTM()
        if MODEL_PATH.exists():
            try:
                _model.load_state_dict(torch.load(MODEL_PATH, map_location=torch.device('cpu')))
            except Exception:
                pass
        _model.eval()
    return _model


def get_acc_current(lat: float) -> tuple[float, float]:
    if lat >= -60.0:
        u = 0.15
    elif lat <= -75.0:
        u = 0.02
    else:
        u = 0.02 + (0.15 - 0.02) * (lat - (-75.0)) / 15.0
    u = max(0.01, min(0.25, u))
    v = 0.01
    return u, v


def get_era5_wind(ds: xr.Dataset | None, lat: float, lon: float) -> tuple[float, float]:
    if ds is None:
        return 3.6, -2.2
    try:
        clamped_lat = max(-75.0, min(-60.0, lat))
        clamped_lon = max(-80.0, min(-30.0, lon))
        pt = ds.sel(latitude=clamped_lat, longitude=clamped_lon, method="nearest")
        u = float(pt['u10'].mean()) if 'u10' in pt else 0.0
        v = float(pt['v10'].mean()) if 'v10' in pt else 0.0
        return u, v
    except Exception:
        return 3.6, -2.2


def predict(lat: float, lon: float, name: str | None = None, hours: list[int] | None = None) -> list[dict]:
    hours = hours or [24, 48, 72]
    
    # 1. Fetch history from database
    real_history = []
    if name and DB_PATH.exists():
        try:
            with sqlite3.connect(DB_PATH) as conn:
                conn.row_factory = sqlite3.Row
                rows = conn.execute(
                    "SELECT lat, lon FROM iceberg_history WHERE name = ? ORDER BY fetched_at DESC LIMIT 14",
                    (name,)
                ).fetchall()
                real_history = [dict(r) for r in rows]
        except Exception:
            pass
            
    # 2. Open ERA5 cache to extract winds
    ds = None
    if ERA5_CACHE.exists():
        try:
            ds = xr.open_dataset(ERA5_CACHE)
        except Exception:
            pass
            
    # 3. Build sequence of length 14 (latest to oldest, then reverse)
    seq = []
    sim_start_lat = lat
    sim_start_lon = lon
    
    for pt in real_history:
        plat, plon = pt["lat"], pt["lon"]
        w_u, w_v = get_era5_wind(ds, plat, plon)
        c_u, c_v = get_acc_current(plat)
        seq.append([plat, plon, w_u, w_v, c_u, c_v])
        sim_start_lat, sim_start_lon = plat, plon
        
    WIND_DRAG = 0.02
    while len(seq) < 14:
        wind_u, wind_v = get_era5_wind(ds, sim_start_lat, sim_start_lon)
        cur_u, cur_v = get_acc_current(sim_start_lat)
        
        # Calculate daily drift vector (forward)
        vel_u = WIND_DRAG * wind_u + cur_u
        vel_v = WIND_DRAG * wind_v + cur_v
        
        dx = vel_u * 86400.0
        dy = vel_v * 86400.0
        
        dlat = dy / 111320.0
        dlon = dx / (111320.0 * math.cos(math.radians(sim_start_lat)))
        
        sim_start_lat = sim_start_lat - dlat
        sim_start_lon = sim_start_lon - dlon
        
        seq.append([sim_start_lat, sim_start_lon, wind_u, wind_v, cur_u, cur_v])
        
    if ds is not None:
        ds.close()
        
    seq = seq[:14]
    seq.reverse()
    
    seq_arr = np.array(seq, dtype=np.float32)
    last_lat = seq_arr[-1, 0]
    last_lon = seq_arr[-1, 1]
    
    seq_arr[:, 0] -= last_lat
    seq_arr[:, 1] -= last_lon
    
    # 4. Run model inference
    x_tensor = torch.tensor(seq_arr).unsqueeze(0)
    model = get_model()
    
    with torch.no_grad():
        preds = model(x_tensor).squeeze(0).numpy()
        
    pred_positions = {
        24: (float(last_lat + preds[0]), float(last_lon + preds[1])),
        48: (float(last_lat + preds[2]), float(last_lon + preds[3])),
        72: (float(last_lat + preds[4]), float(last_lon + preds[5])),
    }
    
    pts = []
    for h in hours:
        p_lat, p_lon = pred_positions.get(h, (lat, lon))
        uncertainty = round(4.5 * math.sqrt(h / 24), 2)
        pts.append({
            "hour": h,
            "lat": round(p_lat, 4),
            "lon": round(p_lon, 4),
            "uncertainty_nm": uncertainty
        })
        
    return pts
