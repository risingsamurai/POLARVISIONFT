# LSTM / IceNet training

## What actually ran

- `train_lstm.py` fitted a least-squares drift head on **38 LIVE BYU icebergs** (760 daily samples from 21-day simulated tracks seeded at the live lat/lon).
- `evaluate.py` mean error: 24h **0.80 nm**, 48h **1.26 nm**, 72h **1.87 nm**. Metrics are in `checkpoints/eval_metrics.json`.
- **PyTorch LSTM was not installed or trained.**
- **`finetune_icenet.py` was not run.** Ice forecasts are persistence + climatology (`backend/ml/icenet_runner.py`), not BAS IceNet weights.
