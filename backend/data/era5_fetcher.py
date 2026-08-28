"""ERA5 wind/current fetcher. Uses CDS if CDS_API_KEY is set; otherwise climatology sample."""

from __future__ import annotations

import argparse
import json
import math
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path

import cdsapi
import xarray as xr
from dotenv import load_dotenv, find_dotenv

# Load environment variables
load_dotenv(find_dotenv(), override=True)

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


def fetch_era5_live(area=None):
    """
    area = [North, West, South, East] bounding box, e.g. Antarctic Peninsula:
    [-60, -80, -75, -30]
    Returns path to downloaded NetCDF file, or raises on failure.
    """
    key = os.getenv("CDS_API_KEY")
    if not key:
        raise ValueError("CDS_API_KEY environment variable is not set")
        
    client = cdsapi.Client(
        url="https://cds.climate.copernicus.eu/api",
        key=key,
    )
    # ERA5 has a ~5 day publication lag; go back 7 days to be safe
    target_date = datetime.now(timezone.utc) - timedelta(days=7)
    dataset = "reanalysis-era5-single-levels"
    request = {
        "product_type": ["reanalysis"],
        "variable": [
            "10m_u_component_of_wind",
            "10m_v_component_of_wind",
        ],
        "year": [target_date.strftime("%Y")],
        "month": [target_date.strftime("%m")],
        "day": [target_date.strftime("%d")],
        "time": ["00:00", "06:00", "12:00", "18:00"],
        "area": area or [-60, -80, -75, -30],
        "data_format": "netcdf",
    }
    target = str(Path(__file__).parent / "cache" / "era5_latest.nc")
    os.makedirs(os.path.dirname(target), exist_ok=True)
    client.retrieve(dataset, request, target)
    return target


def run() -> dict:
    live = False
    error = None
    data = None
    
    try:
        target = fetch_era5_live()
        # Open downloaded NetCDF file using xarray
        with xr.open_dataset(target) as ds:
            lat_name = 'latitude' if 'latitude' in ds.coords else 'lat'
            lon_name = 'longitude' if 'longitude' in ds.coords else 'lon'
            
            # Select first time index if time-like dimension is present
            time_dim = None
            for dim in ['valid_time', 'time', 'forecast_time']:
                if dim in ds.dims:
                    time_dim = dim
                    break
            if time_dim:
                ds_time = ds.isel({time_dim: 0})
            else:
                ds_time = ds
                
            vectors = []
            for lat in [ -62 + 0.5 * k for k in range(18)]:
                for lon in [ -58 + 0.7 * k for k in range(22)]:
                    # Select nearest coordinate point
                    pt = ds_time.sel({lat_name: lat, lon_name: lon}, method='nearest')
                    u = float(pt['u10'].mean()) if 'u10' in pt else 0.0
                    v = float(pt['v10'].mean()) if 'v10' in pt else 0.0
                    
                    # Generative fallback for current_u and current_v
                    cur_u = 0.15 * math.sin(math.radians(lon))
                    cur_v = 0.22 * math.cos(math.radians(lat))
                    
                    vectors.append(
                        {
                            "lat": round(lat, 3),
                            "lon": round(lon, 3),
                            "wind_u": round(u, 3),
                            "wind_v": round(v, 3),
                            "current_u": round(cur_u, 3),
                            "current_v": round(cur_v, 3),
                        }
                    )
            data = {"vectors": vectors}
            live = True
    except Exception as exc:
        error = str(exc)
        data = climatology()
        
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
