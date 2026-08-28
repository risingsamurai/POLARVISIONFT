"""Evaluate the trained PyTorch LSTM model on holdout trajectories.

Calculates the mean positional prediction error in kilometers (using Haversine formula)
for 24h, 48h, and 72h horizons.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
import numpy as np
import pandas as pd
import torch
import torch.nn as nn

# Paths
ROOT = Path(__file__).resolve().parents[1]
DATASET_PATH = Path(__file__).parent / "synthetic_drift_dataset.csv"
MODEL_PATH = ROOT / "backend" / "ml" / "lstm_weights.pt"
METRICS_PATH = Path(__file__).parent / "checkpoints" / "eval_metrics.json"


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


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    la1 = math.radians(lat1)
    la2 = math.radians(lat2)
    h = math.sin(dlat / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin(dlon / 2) ** 2
    return 2 * r * math.asin(min(1.0, math.sqrt(h)))


def main():
    if not DATASET_PATH.exists():
        raise FileNotFoundError(f"Missing dataset at {DATASET_PATH}")
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"Missing model weights at {MODEL_PATH}. Run train_lstm.py first.")
        
    # Load Model
    model = IcebergLSTM()
    model.load_state_dict(torch.load(MODEL_PATH))
    model.eval()
    
    df = pd.read_csv(DATASET_PATH)
    unique_ids = sorted(df["iceberg_id"].unique())
    
    # Holdout icebergs: last 8 icebergs (indices 30 to 37)
    holdout_ids = unique_ids[30:]
    print(f"Evaluating on {len(holdout_ids)} holdout icebergs: {holdout_ids}")
    
    errors = {24: [], 48: [], 72: []}
    
    for berg_id in holdout_ids:
        berg_df = df[df["iceberg_id"] == berg_id].sort_values("day")
        if len(berg_df) < 30:
            continue
            
        coords = berg_df[["lat", "lon", "wind_u", "wind_v", "current_u", "current_v"]].values
        
        # We extract all 14 overlapping 17-day windows to get robust evaluation statistics
        for start_idx in range(30 - 17 + 1):
            window = coords[start_idx : start_idx + 17]
            
            # Input sequence (first 14 steps)
            seq = window[:14].copy()
            last_lat = seq[-1, 0]
            last_lon = seq[-1, 1]
            
            # Center coordinates
            seq[:, 0] -= last_lat
            seq[:, 1] -= last_lon
            
            # Prepare tensor input
            x_tensor = torch.tensor(seq.astype(np.float32)).unsqueeze(0) # shape: (1, 14, 6)
            
            with torch.no_grad():
                preds = model(x_tensor).squeeze(0).numpy() # shape: (6,)
                
            # Absolute predicted positions
            pred_lat_24 = last_lat + preds[0]
            pred_lon_24 = last_lon + preds[1]
            pred_lat_48 = last_lat + preds[2]
            pred_lon_48 = last_lon + preds[3]
            pred_lat_72 = last_lat + preds[4]
            pred_lon_72 = last_lon + preds[5]
            
            # Real positions
            real_lat_24 = window[14, 0]
            real_lon_24 = window[14, 1]
            real_lat_48 = window[15, 0]
            real_lon_48 = window[15, 1]
            real_lat_72 = window[16, 0]
            real_lon_72 = window[16, 1]
            
            # Calculate errors in km
            errors[24].append(haversine_km(pred_lat_24, pred_lon_24, real_lat_24, real_lon_24))
            errors[48].append(haversine_km(pred_lat_48, pred_lon_48, real_lat_48, real_lon_48))
            errors[72].append(haversine_km(pred_lat_72, pred_lon_72, real_lat_72, real_lon_72))
            
    summary = {
        "n_holdout_icebergs": len(holdout_ids),
        "mean_error_km": {str(h): round(float(np.mean(errors[h])), 2) for h in errors},
        "median_error_km": {str(h): round(float(np.median(errors[h])), 2) for h in errors},
    }
    
    METRICS_PATH.parent.mkdir(parents=True, exist_ok=True)
    METRICS_PATH.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
