"""Train a PyTorch LSTM model on physics-informed synthetic drift trajectories.

Inputs: Sequence of 14 days of [lat, lon, wind_u, wind_v, current_u, current_v] (centered).
Outputs: Predicted relative lat/lon offsets at t+24h, t+48h, t+72h.
"""

from __future__ import annotations

import json
from pathlib import Path
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim

# Paths
ROOT = Path(__file__).resolve().parents[1]
DATASET_PATH = Path(__file__).parent / "synthetic_drift_dataset.csv"
MODEL_PATH = ROOT / "backend" / "ml" / "lstm_weights.pt"


class IcebergLSTM(nn.Module):
    def __init__(self, input_size=6, hidden_size=32, num_layers=1, output_size=6):
        super().__init__()
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True)
        self.fc = nn.Linear(hidden_size, output_size)
        
    def forward(self, x):
        # x shape: (batch_size, seq_len=14, input_size=6)
        out, _ = self.lstm(x)
        # Take the output of the last time step
        last_out = out[:, -1, :]
        preds = self.fc(last_out)
        return preds


def prepare_sequences(df: pd.DataFrame, iceberg_ids: list[str]) -> tuple[torch.Tensor, torch.Tensor]:
    X_list = []
    Y_list = []
    
    for berg_id in iceberg_ids:
        berg_df = df[df["iceberg_id"] == berg_id].sort_values("day")
        # Ensure we have a complete 30-day sequence
        if len(berg_df) < 30:
            continue
            
        coords = berg_df[["lat", "lon", "wind_u", "wind_v", "current_u", "current_v"]].values
        
        # Overlapping 17-day windows
        # Day 0 to 16, Day 1 to 17, ..., Day 13 to 29
        for start_idx in range(30 - 17 + 1):
            window = coords[start_idx : start_idx + 17] # shape: (17, 6)
            
            # Input sequence: first 14 steps
            seq = window[:14].copy() # shape: (14, 6)
            
            # Last known position in the input sequence
            last_lat = seq[-1, 0]
            last_lon = seq[-1, 1]
            
            # Center coordinates around the last step
            seq[:, 0] -= last_lat
            seq[:, 1] -= last_lon
            
            # Target output: relative lat/lon displacements for days 14, 15, 16
            target_lat_24 = window[14, 0] - last_lat
            target_lon_24 = window[14, 1] - last_lon
            target_lat_48 = window[15, 0] - last_lat
            target_lon_48 = window[15, 1] - last_lon
            target_lat_72 = window[16, 0] - last_lat
            target_lon_72 = window[16, 1] - last_lon
            
            target = np.array([
                target_lat_24, target_lon_24,
                target_lat_48, target_lon_48,
                target_lat_72, target_lon_72
            ], dtype=np.float32)
            
            X_list.append(seq.astype(np.float32))
            Y_list.append(target)
            
    return torch.tensor(np.array(X_list)), torch.tensor(np.array(Y_list))


def train():
    if not DATASET_PATH.exists():
        raise FileNotFoundError(f"Missing dataset at {DATASET_PATH}. Run generate_synthetic_trajectories.py first.")
        
    df = pd.read_csv(DATASET_PATH)
    unique_ids = sorted(df["iceberg_id"].unique())
    
    # Train on first 30 icebergs, hold out last 8 for evaluation
    train_ids = unique_ids[:30]
    print(f"Training on {len(train_ids)} icebergs, holding out {len(unique_ids) - len(train_ids)} for evaluation.")
    
    X_train, Y_train = prepare_sequences(df, train_ids)
    print(f"Dataset prepared. X_train shape: {X_train.shape}, Y_train shape: {Y_train.shape}")
    
    # Initialize Model, Loss, and Optimizer
    model = IcebergLSTM()
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=0.005)
    
    epochs = 100
    batch_size = 32
    
    print("Starting LSTM training...")
    for epoch in range(1, epochs + 1):
        model.train()
        permutation = torch.randperm(X_train.size(0))
        epoch_loss = 0.0
        
        for i in range(0, X_train.size(0), batch_size):
            indices = permutation[i : i + batch_size]
            batch_x, batch_y = X_train[indices], Y_train[indices]
            
            optimizer.zero_grad()
            preds = model(batch_x)
            loss = criterion(preds, batch_y)
            loss.backward()
            optimizer.step()
            
            epoch_loss += loss.item() * batch_x.size(0)
            
        epoch_loss /= X_train.size(0)
        if epoch == 1 or epoch % 10 == 0:
            print(f"Epoch {epoch:03d}/{epochs:03d} | Loss: {epoch_loss:.6f}")
            
    # Save trained model weights
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), MODEL_PATH)
    print(f"Successfully saved LSTM weights to {MODEL_PATH}")


if __name__ == "__main__":
    train()
