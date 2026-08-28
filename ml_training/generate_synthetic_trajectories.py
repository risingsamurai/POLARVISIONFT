"""Generate physics-informed synthetic trajectories for BYU icebergs using ERA5 and ACC current.

Simulates 30 days of drift backward in time from today's real seed positions.
Uses a 2% wind drag coefficient and a parameterized Antarctic Circumpolar Current.
"""

from __future__ import annotations

import json
import math
import random
from pathlib import Path
import numpy as np
import pandas as pd
import xarray as xr

# Paths
ROOT = Path(__file__).resolve().parents[1]
BYU_CACHE = ROOT / "backend" / "data" / "cache" / "byu_icebergs.json"
ERA5_CACHE = ROOT / "backend" / "data" / "cache" / "era5_latest.nc"
OUTPUT_CSV = Path(__file__).parent / "synthetic_drift_dataset.csv"


def get_acc_current(lat: float) -> tuple[float, float]:
    """
    Antarctic Circumpolar Current parameterization:
    Stronger near ~60°S (0.15 m/s), weaker near the continent (~75°S, 0.02 m/s).
    """
    if lat >= -60.0:
        u = 0.15
    elif lat <= -75.0:
        u = 0.02
    else:
        u = 0.02 + (0.15 - 0.02) * (lat - (-75.0)) / 15.0
    u = max(0.01, min(0.25, u))
    # Small northward component representing Ekman transport
    v = 0.01
    return u, v


def get_era5_wind(ds: xr.Dataset, lat: float, lon: float) -> tuple[float, float]:
    # clamp coordinates to grid bounds
    clamped_lat = max(-75.0, min(-60.0, lat))
    clamped_lon = max(-80.0, min(-30.0, lon))
    
    pt = ds.sel(latitude=clamped_lat, longitude=clamped_lon, method="nearest")
    u = float(pt['u10'].mean()) if 'u10' in pt else 0.0
    v = float(pt['v10'].mean()) if 'v10' in pt else 0.0
    return u, v


def main():
    if not BYU_CACHE.exists():
        raise FileNotFoundError(f"Missing BYU Cache file at {BYU_CACHE}")
    if not ERA5_CACHE.exists():
        raise FileNotFoundError(f"Missing ERA5 Cache file at {ERA5_CACHE}")
        
    byu_data = json.loads(BYU_CACHE.read_text(encoding="utf-8"))
    icebergs = byu_data["icebergs"]
    
    ds = xr.open_dataset(ERA5_CACHE)
    
    records = []
    WIND_DRAG = 0.02
    random.seed(42)
    
    for berg in icebergs:
        berg_name = berg["name"]
        curr_lat = berg["lat"]
        curr_lon = berg["lon"]
        
        states = []
        lat = curr_lat
        lon = curr_lon
        
        # Simulate 30 days: day 29 down to day 0
        for day in range(29, -1, -1):
            wind_u, wind_v = get_era5_wind(ds, lat, lon)
            cur_u, cur_v = get_acc_current(lat)
            
            states.append((berg_name, day, lat, lon, wind_u, wind_v, cur_u, cur_v))
            
            if day == 0:
                break
                
            vel_u = WIND_DRAG * wind_u + cur_u
            vel_v = WIND_DRAG * wind_v + cur_v
            
            dx = vel_u * 86400.0
            dy = vel_v * 86400.0
            
            step_len = math.sqrt(dx**2 + dy**2)
            noise_std = max(500.0, 0.05 * step_len)
            noise_x = random.gauss(0.0, noise_std)
            noise_y = random.gauss(0.0, noise_std)
            
            dx_noisy = dx + noise_x
            dy_noisy = dy + noise_y
            
            dlat = dy_noisy / 111320.0
            dlon = dx_noisy / (111320.0 * math.cos(math.radians(lat)))
            
            lat = lat - dlat
            lon = lon - dlon
            
        states.reverse()
        records.extend(states)
        
    df = pd.DataFrame(records, columns=["iceberg_id", "day", "lat", "lon", "wind_u", "wind_v", "current_u", "current_v"])
    df.to_csv(OUTPUT_CSV, index=False)
    print(f"Generated synthetic trajectories dataset with {len(df)} rows at {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
