# LSTM / IceNet training

## What actually ran (2026-09-07)

- Dataset: `merged_trajectories.csv` (516,646 `real_historical` + 1,140 `synthetic_physics`).
- `train_lstm.py` HybridIcebergLSTM, 40 epochs, Adam lr=0.003, batch 256.
  - Loss: 0.031165 (ep1) → 0.024791 (10) → 0.023227 (20) → 0.022473 (30) → 0.021653 (40).
- `evaluate.py` holdout 103 icebergs, 24,109 windows. Mean km with size: 24h 3.20, 48h 5.82, 72h 8.19.
- Historical training wind/current are parameterized, not dated ERA5. Live inference uses `era5_latest.nc`.
- **`finetune_icenet.py` was not run.** Ice forecasts remain persistence + climatology.

Older least-squares / 0.80 nm numbers in this file were from an earlier phase and are obsolete.
