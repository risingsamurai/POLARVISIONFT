# POLARIS — Data Sources

Auth requirements, rate limits, fallback sample locations, and the **Data Reality Table** (source of truth for live vs cached).

## Fetchers

| Source | Fetcher | Auth | Rate limits | Sample / cache path |
|---|---|---|---|---|
| NSIDC (NOAA) | `backend/data/nsidc_fetcher.py` | Earthdata optional | None | `backend/data/samples/nsidc_sic_sample.json` |
| BYU/NIC | `backend/data/byu_scraper.py` | None | Polite 6h schedule | `backend/data/samples/byu_icebergs_sample.json` |
| ERA5 (CDS) | `backend/data/era5_fetcher.py` | `CDS_API_KEY` | **120 requests/day** | `backend/data/samples/era5_sample.json`; live NetCDF `backend/data/cache/era5_latest.nc` |

## Data Reality Table

Updated 2026-09-07 after a live CDS retrieve (request `92cde1af-a4c1-4bac-8205-06733a47c527`) wrote `era5_latest.nc` (242,614 bytes, 01:11:35 local).

| Source | Status right now | Last successful live fetch | Why (if fallback) |
|---|---|---|---|
| NSIDC | LIVE (this session, 2026-09-07) | Startup ingest | Direct HTTPS G10016-style grid |
| BYU/NIC | LIVE | Startup ingest | Scraped current iceberg table; SQLite count = 38 |
| ERA5 | **LIVE** | 2026-09-07 CDS retrieve | Startup ingest earlier this session **failed** with `CDS_API_KEY environment variable is not set` because `.env` was empty (0 bytes). `OFFLINE_STARTUP` was **not** set. The scheduled job **did** run; it fell back to climatology JSON and **did not** write `era5_latest.nc`. After restoring `.env` and calling `era5_fetcher.run()` directly, NetCDF exists and live LSTM wind is nearest-neighbor `u10`/`v10` (not the 3.6, −2.2 fallback). |

## Pipeline (this run)

Startup ingest in FastAPI lifespan: BYU scrape → SQLite `icebergs` + `iceberg_history` → NSIDC + ERA5 (`fetch_era5_live` → `era5_latest.nc`) → in-process cache. APScheduler interval job `ingest_all` is registered for `INGEST_INTERVAL_HOURS` (default 6). Redis optional; in-memory dict if Redis is down.

Local iceberg store is SQLite `backend/polaris.db`.

## LSTM training data vs live inference wind

- **Training set:** `ml_training/merged_trajectories.csv` = 516,646 `real_historical` rows (646 BYU icebergs, calendar dates 1976–2026) **plus** 1,140 `synthetic_physics` rows (38 live-seeded 30-day backdated tracks).
- **Historical rows' wind/current:** parameterized from lat/lon (`compute_drift_vectors` in `parse_byu_historical.py`). **Not** measured ERA5 for those 14,421 historical dates. A 51-year CDS backfill was assessed as impractical (dozens of large queued requests) within the project timeline. This is a deliberate limitation.
- **Synthetic rows' wind:** sampled from **current** `era5_latest.nc` at the simulated position; positions are backdated with 2% wind drag + parameterized ACC + noise (`generate_synthetic_trajectories.py`).
- **LIVE app predictions** (`GET /api/icebergs/` → `lstm_predictor.predict`): wind from **current** ERA5 NetCDF (`u10`/`v10` nearest neighbor). That is genuinely different from historical training wind.
- **Ocean current (training historical, synthetic, and live):** parameterized Antarctic Circumpolar Current (`get_acc_current` for live/synthetic; lat/lon trig formula on historical rows). Not measured current.

Holdout metrics after merged retraining (2026-09-07) are in `DEVIATIONS.md` and `ml_training/checkpoints/eval_metrics.json`.
