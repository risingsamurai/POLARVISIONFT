"""Evaluate the trained Hybrid PyTorch LSTM model on real BYU holdout trajectories.

Calculates the mean positional prediction error in kilometers (using Haversine formula)
for 24h, 48h, and 72h horizons on unobserved holdout icebergs, and performs an ablation
study comparing performance with vs. without the static iceberg size feature.
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
DATASET_PATH = Path(__file__).parent / "merged_trajectories.csv"
MODEL_PATH = ROOT / "backend" / "ml" / "lstm_weights.pt"
METRICS_PATH = Path(__file__).parent / "checkpoints" / "eval_metrics.json"


class HybridIcebergLSTM(nn.Module):
    def __init__(self, seq_input_size=6, static_input_size=1, hidden_size=32, output_size=6):
        super().__init__()
        self.lstm = nn.LSTM(seq_input_size, hidden_size, num_layers=1, batch_first=True)
        self.size_fc = nn.Linear(static_input_size, 8)
        self.relu = nn.ReLU()
        self.fc1 = nn.Linear(hidden_size + 8, 32)
        self.fc2 = nn.Linear(32, output_size)

    def forward(self, x_seq, x_static):
        out, _ = self.lstm(x_seq)
        last_out = out[:, -1, :]
        size_emb = self.relu(self.size_fc(x_static))
        combined = torch.cat([last_out, size_emb], dim=1)
        h = self.relu(self.fc1(combined))
        preds = self.fc2(h)
        return preds


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    la1 = math.radians(lat1)
    la2 = math.radians(lat2)
    h = math.sin(dlat / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin(dlon / 2) ** 2
    return 2 * r * math.asin(min(1.0, math.sqrt(h)))


def prepare_holdout_windows(df: pd.DataFrame, holdout_ids: list[str]) -> tuple[torch.Tensor, torch.Tensor, list[tuple]]:
    """Generates test windows from holdout icebergs."""
    X_seq_list = []
    X_static_list = []
    targets_info = []  # (source, last_lat, last_lon, real_lat_24, ... real_lon_72)

    grouped = df.groupby("iceberg_id")
    target_ids = set(holdout_ids)

    for berg_id in target_ids:
        if berg_id not in grouped.groups:
            continue
        berg_df = grouped.get_group(berg_id).sort_values("date")
        if len(berg_df) < 17:
            continue

        source = str(berg_df["source"].iloc[0]) if "source" in berg_df.columns else "unknown"
        coords = berg_df[["lat", "lon", "wind_u", "wind_v", "current_u", "current_v"]].values
        sizes = berg_df["size_nm"].values

        for start_idx in range(0, len(berg_df) - 17 + 1, 3):
            window_coords = coords[start_idx : start_idx + 17]
            window_sizes = sizes[start_idx : start_idx + 17]

            seq = window_coords[:14].copy()
            last_lat = seq[-1, 0]
            last_lon = seq[-1, 1]

            # Center lat/lon
            seq[:, 0] -= last_lat
            seq[:, 1] -= last_lon

            mean_size = float(np.mean(window_sizes[:14])) / 10.0

            real_lat_24, real_lon_24 = window_coords[14, 0], window_coords[14, 1]
            real_lat_48, real_lon_48 = window_coords[15, 0], window_coords[15, 1]
            real_lat_72, real_lon_72 = window_coords[16, 0], window_coords[16, 1]

            # Filter unrealistic jumps
            max_disp = max(
                abs(real_lat_24 - last_lat), abs(real_lon_24 - last_lon),
                abs(real_lat_48 - last_lat), abs(real_lon_48 - last_lon),
                abs(real_lat_72 - last_lat), abs(real_lon_72 - last_lon),
            )
            if max_disp > 5.0:
                continue

            X_seq_list.append(seq.astype(np.float32))
            X_static_list.append(np.array([mean_size], dtype=np.float32))
            targets_info.append((
                source,
                last_lat, last_lon,
                real_lat_24, real_lon_24,
                real_lat_48, real_lon_48,
                real_lat_72, real_lon_72
            ))

    return (
        torch.tensor(np.array(X_seq_list)),
        torch.tensor(np.array(X_static_list)),
        targets_info
    )


def evaluate():
    if not DATASET_PATH.exists():
        raise FileNotFoundError(f"Missing dataset at {DATASET_PATH}")
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"Missing model weights at {MODEL_PATH}. Wait for training to finish.")

    df = pd.read_csv(DATASET_PATH)
    unique_ids = sorted(df["iceberg_id"].unique())

    # Same split as train_lstm.py
    np.random.seed(42)
    shuffled_ids = np.random.permutation(unique_ids)
    split_idx = int(len(shuffled_ids) * 0.85)
    holdout_ids = list(shuffled_ids[split_idx:])

    print(f"Evaluating model on {len(holdout_ids)} holdout icebergs...")

    model = HybridIcebergLSTM()
    model.load_state_dict(torch.load(MODEL_PATH))
    model.eval()

    X_seq, X_static, targets_info = prepare_holdout_windows(df, holdout_ids)
    print(f"Holdout dataset prepared: {X_seq.size(0)} evaluation windows.")

    with torch.no_grad():
        # Full model prediction (with size feature)
        preds_with_size = model(X_seq, X_static).numpy()

        # Ablation prediction (without size feature / size set to 0.0)
        X_static_zero = torch.zeros_like(X_static)
        preds_without_size = model(X_seq, X_static_zero).numpy()

    errors_with = {24: [], 48: [], 72: []}
    errors_without = {24: [], 48: [], 72: []}
    errors_with_by_source: dict[str, dict[int, list]] = {}
    errors_without_by_source: dict[str, dict[int, list]] = {}

    for idx, info in enumerate(targets_info):
        source, last_lat, last_lon, r_lat24, r_lon24, r_lat48, r_lon48, r_lat72, r_lon72 = info
        if source not in errors_with_by_source:
            errors_with_by_source[source] = {24: [], 48: [], 72: []}
            errors_without_by_source[source] = {24: [], 48: [], 72: []}

        # Predictions WITH size feature
        p_with = preds_with_size[idx]
        plat24_w, plon24_w = last_lat + p_with[0], last_lon + p_with[1]
        plat48_w, plon48_w = last_lat + p_with[2], last_lon + p_with[3]
        plat72_w, plon72_w = last_lat + p_with[4], last_lon + p_with[5]

        e24 = haversine_km(plat24_w, plon24_w, r_lat24, r_lon24)
        e48 = haversine_km(plat48_w, plon48_w, r_lat48, r_lon48)
        e72 = haversine_km(plat72_w, plon72_w, r_lat72, r_lon72)
        errors_with[24].append(e24)
        errors_with[48].append(e48)
        errors_with[72].append(e72)
        errors_with_by_source[source][24].append(e24)
        errors_with_by_source[source][48].append(e48)
        errors_with_by_source[source][72].append(e72)

        # Predictions WITHOUT size feature
        p_wo = preds_without_size[idx]
        plat24_wo, plon24_wo = last_lat + p_wo[0], last_lon + p_wo[1]
        plat48_wo, plon48_wo = last_lat + p_wo[2], last_lon + p_wo[3]
        plat72_wo, plon72_wo = last_lat + p_wo[4], last_lon + p_wo[5]

        e24n = haversine_km(plat24_wo, plon24_wo, r_lat24, r_lon24)
        e48n = haversine_km(plat48_wo, plon48_wo, r_lat48, r_lon48)
        e72n = haversine_km(plat72_wo, plon72_wo, r_lat72, r_lon72)
        errors_without[24].append(e24n)
        errors_without[48].append(e48n)
        errors_without[72].append(e72n)
        errors_without_by_source[source][24].append(e24n)
        errors_without_by_source[source][48].append(e48n)
        errors_without_by_source[source][72].append(e72n)

    def _pack(err_map: dict[int, list]) -> dict:
        return {
            "n_windows": len(err_map[24]),
            "mean_error_km": {str(h): round(float(np.mean(err_map[h])), 2) if err_map[h] else None for h in (24, 48, 72)},
            "median_error_km": {str(h): round(float(np.median(err_map[h])), 2) if err_map[h] else None for h in (24, 48, 72)},
        }

    summary = {
        "n_holdout_icebergs": len(holdout_ids),
        "n_holdout_windows": len(targets_info),
        "mean_error_km_with_size": {str(h): round(float(np.mean(errors_with[h])), 2) for h in errors_with},
        "median_error_km_with_size": {str(h): round(float(np.median(errors_with[h])), 2) for h in errors_with},
        "ablation_without_size": {
            "mean_error_km": {str(h): round(float(np.mean(errors_without[h])), 2) for h in errors_without},
            "median_error_km": {str(h): round(float(np.median(errors_without[h])), 2) for h in errors_without},
        },
        "by_source_with_size": {src: _pack(errs) for src, errs in sorted(errors_with_by_source.items())},
        "by_source_ablation_without_size": {src: _pack(errs) for src, errs in sorted(errors_without_by_source.items())},
    }

    METRICS_PATH.parent.mkdir(parents=True, exist_ok=True)
    METRICS_PATH.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print("\n--- HOLD OUT EVALUATION & ABLATION RESULTS ---")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    evaluate()
