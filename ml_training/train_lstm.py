"""Train a PyTorch hybrid LSTM model on merged real-historical + synthetic trajectories.

Inputs:
  - Sequence (14 days): [lat, lon, wind_u, wind_v, current_u, current_v] (centered coordinates).
  - Static Feature: size_nm (iceberg diameter in NM).
Outputs: Predicted relative lat/lon displacements at t+24h, t+48h, t+72h.
"""

from __future__ import annotations

import json
from pathlib import Path
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim

ROOT = Path(__file__).resolve().parents[1]
DATASET_PATH = Path(__file__).parent / "merged_trajectories.csv"
MODEL_PATH = ROOT / "backend" / "ml" / "lstm_weights.pt"
CHECKPOINT_PATH = Path(__file__).parent / "checkpoints" / "lstm_weights.pt"


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
        last_out = out[:, -1, :]  # (batch, 32)
        size_emb = self.relu(self.size_fc(x_static))  # (batch, 8)
        combined = torch.cat([last_out, size_emb], dim=1)  # (batch, 40)
        h = self.relu(self.fc1(combined))
        preds = self.fc2(h)  # (batch, 6)
        return preds


def prepare_historical_dataset(df: pd.DataFrame, iceberg_ids: list[str]) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    X_seq_list = []
    X_static_list = []
    Y_list = []

    target_ids = set(iceberg_ids)
    grouped = df.groupby("iceberg_id")

    for berg_id in target_ids:
        if berg_id not in grouped.groups:
            continue
        berg_df = grouped.get_group(berg_id).sort_values("date")
        if len(berg_df) < 17:
            continue

        coords = berg_df[["lat", "lon", "wind_u", "wind_v", "current_u", "current_v"]].values
        sizes = berg_df["size_nm"].values

        # Sample windows with stride 10 for fast, clean CPU training
        for start_idx in range(0, len(berg_df) - 17 + 1, 10):
            window_coords = coords[start_idx : start_idx + 17]
            window_sizes = sizes[start_idx : start_idx + 17]

            seq = window_coords[:14].copy()
            last_lat = seq[-1, 0]
            last_lon = seq[-1, 1]

            # Center lat/lon around the last time step
            seq[:, 0] -= last_lat
            seq[:, 1] -= last_lon

            # Static size feature (normalized by dividing by 10.0)
            mean_size = float(np.mean(window_sizes[:14])) / 10.0

            # Target 24h, 48h, 72h displacements
            target_lat_24 = window_coords[14, 0] - last_lat
            target_lon_24 = window_coords[14, 1] - last_lon
            target_lat_48 = window_coords[15, 0] - last_lat
            target_lon_48 = window_coords[15, 1] - last_lon
            target_lat_72 = window_coords[16, 0] - last_lat
            target_lon_72 = window_coords[16, 1] - last_lon

            target = np.array([
                target_lat_24, target_lon_24,
                target_lat_48, target_lon_48,
                target_lat_72, target_lon_72
            ], dtype=np.float32)

            # Filter unrealistic jumps (teleportation artifacts)
            if np.max(np.abs(target)) > 5.0:
                continue

            X_seq_list.append(seq.astype(np.float32))
            X_static_list.append(np.array([mean_size], dtype=np.float32))
            Y_list.append(target)

    return (
        torch.tensor(np.array(X_seq_list)),
        torch.tensor(np.array(X_static_list)),
        torch.tensor(np.array(Y_list))
    )


def train():
    if not DATASET_PATH.exists():
        raise FileNotFoundError(f"Missing dataset at {DATASET_PATH}.")

    print(f"Loading dataset from {DATASET_PATH}...")
    df = pd.read_csv(DATASET_PATH)
    unique_ids = sorted(df["iceberg_id"].unique())

    # Reserve 15% of icebergs for holdout evaluation
    np.random.seed(42)
    shuffled_ids = np.random.permutation(unique_ids)
    split_idx = int(len(shuffled_ids) * 0.85)

    train_ids = shuffled_ids[:split_idx]
    holdout_ids = shuffled_ids[split_idx:]

    print(f"Training on {len(train_ids)} icebergs, holding out {len(holdout_ids)} for evaluation.")
    print(f"Source counts in full dataset: {df.groupby('source')['iceberg_id'].nunique().to_dict() if 'source' in df.columns else 'n/a'}")

    X_seq_train, X_static_train, Y_train = prepare_historical_dataset(df, list(train_ids))
    print(f"Dataset prepared. X_seq: {X_seq_train.shape}, X_static: {X_static_train.shape}, Y: {Y_train.shape}")

    model = HybridIcebergLSTM()
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=0.003)

    epochs = 40
    batch_size = 256

    print("\nStarting Hybrid PyTorch LSTM Training on merged trajectories...")
    for epoch in range(1, epochs + 1):
        model.train()
        permutation = torch.randperm(X_seq_train.size(0))
        epoch_loss = 0.0

        for i in range(0, X_seq_train.size(0), batch_size):
            indices = permutation[i : i + batch_size]
            b_seq, b_stat, b_y = X_seq_train[indices], X_static_train[indices], Y_train[indices]

            optimizer.zero_grad()
            preds = model(b_seq, b_stat)
            loss = criterion(preds, b_y)
            loss.backward()
            optimizer.step()

            epoch_loss += loss.item() * b_seq.size(0)

        epoch_loss /= X_seq_train.size(0)
        if epoch == 1 or epoch % 10 == 0 or epoch == epochs:
            print(f"Epoch {epoch:03d}/{epochs:03d} | Loss: {epoch_loss:.6f}")

    # Save model weights to both backend and checkpoints
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    CHECKPOINT_PATH.parent.mkdir(parents=True, exist_ok=True)

    torch.save(model.state_dict(), MODEL_PATH)
    torch.save(model.state_dict(), CHECKPOINT_PATH)
    print(f"\nSuccessfully saved trained LSTM weights to:\n - {MODEL_PATH}\n - {CHECKPOINT_PATH}")


if __name__ == "__main__":
    train()
