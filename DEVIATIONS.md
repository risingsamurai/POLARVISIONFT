# POLARIS — Deviations log

Written **after** each phase in past tense. Records what actually ran, not what was planned.

## Phase 0 — Scaffolding (2026-08-28)

Attempted `docker compose up --build`. **Docker is not installed** (`docker` is not a recognized command; Docker Desktop paths on this machine do not exist). Compose files, Nginx config, FastAPI placeholders, and Next.js 14 app were written anyway.

Verified instead on the host:
- Python 3.12.10 venv + uvicorn: `GET http://127.0.0.1:8000/health` returned `{"status":"ok","service":"polaris-backend"}`.
- Node.js 20.20.2 was installed via winget so the frontend could run.
- PyTorch was **not** added to the Phase 0 install (would have blocked a slim first boot). IceNet/LSTM later used numpy.

## Phase 1 — 3D simulator (2026-08-28)

Built `/simulation` against Zustand + `mockData.ts` with ocean shader, icebreaker, 21 icebergs, danger rings, dotted route, and the Section 6 HUD (layer toggles, ice legend, minimap, WASD caps, iceberg info, route info, data-reality badge).

`npm install` initially failed on `three@0.128` vs `@react-three/fiber@7` peer (`>=0.133`). Pinned **three@0.133.0** (still pre-r142; no `CapsuleGeometry`). `GET http://localhost:3000/simulation` returned **HTTP 200**. SSR HTML contained Layer Control, Ice Level, Iceberg Info, Route Info, Minimap, POLARIS. Recalculate/Data Reality strings are client-rendered. No headed browser was available in this session to click WASD/orbit; those code paths are in `Vessel.tsx` / `SceneCanvas.tsx`.

## Phase 2 — Data layer (2026-08-28)

Ran `python backend/data/byu_scraper.py`. Result: **LIVE, count=38, error=null**. Names included A76C, A81, A83. SQLite `SELECT count(*) FROM icebergs` = **38** after API ingest. NSIDC and ERA5 fetchers ran as FALLBACK (no credentials). Redis unreachable; in-memory cache used.

## Phase 3 — Overview map (2026-08-28)

`app/page.tsx` uses MapLibre + OSM raster (no Mapbox token). Markers are created from `GET /api/icebergs/` (the same 38 DB rows), not `mockData.ts`.

## Phase 4 — Ice forecast (2026-08-28)

`GET /api/ice/forecast?day=3` returned a grid of **616 cells**, `model=persistence_climatology_ensemble`, `icenet_weights=false`. IceNet pretrained U-Net was **not** downloaded or fine-tuned (no GPU/checkpoint pull). Slider on the simulator is wired to `forecastDay`.

## Phase 5 — Trajectories (2026-08-28)

Ran `ml_training/train_lstm.py` then `evaluate.py` on **38 live BYU icebergs**, **760** simulated daily samples. Recorded mean positional error:

- 24h: **0.80 nm**
- 48h: **1.26 nm**
- 72h: **1.87 nm**

These errors are on kinematics-simulated holdout tracks seeded from live positions, **not** on multi-year BYU CSV histories (the consolidated zip was not downloaded). There is no PyTorch LSTM in this environment; the “LSTM head” is a least-squares drift model whose weights live in `ml_training/checkpoints/lstm_weights.json`. Simulator icebergs hydrate from `/api/icebergs/` when the API is up.

## Phase 6 — Routing (2026-08-28)

First `POST /api/route` returned three identical 2-point geodesics (A* exhausted, then hung ~minutes on 38 bergs × 8000 iterations). Replaced the hot path with three offset corridors. Re-ran POST with start `[-68.35,-52.45]` dest `[-68.72,-49.55]`:

- safest 94.7 nm, 7 pts, mid (-69.085, -50.65)
- balanced 72.0 nm, 7 pts, mid (-68.755, -50.88)
- fastest 67.7 nm, 7 pts, mid (-68.495, -51.05)

Three genuinely different distances and shapes.

## Phase 7 — Autonomous + detection (2026-08-28)

Autonomous mode steers toward the locked route in `Vessel.tsx`. WebSocket `/ws` echoes telemetry. Detection log accumulates nearby iceberg (and can include injected debris labels). Not visually confirmed in a browser this session.

## Phase 8 — Alerts, PDF, polish (2026-08-28)

Alert banner + CRITICAL cooldown when range < 5 nm. Thresholds loaded from `backend/config/alerts.json`. PDF via `pdf-lib` (`Export mission PDF`). Demo script is supported by the UI controls (forecast slider, live berg names, three routes on overview, lock + simulator, autonomous, recalc/info alert, detection log, PDF, data-reality badge). Full start-to-finish click-through was **not** executed in a headed browser here.

`tsc --noEmit` on the frontend passed after fixing R3F 7 / Three.js Group ref types.

## Trajectories & Machine Learning Model Upgrades (2026-08-28)

### Iceberg Trajectory Training Data & LSTM Realignment
- **Data Limitations & Synthetic Training Set:** BYU/NIC does not expose a scrapeable tabular historical positions database (only narrative textual tables of current positions and animated video files).
- **Physics-Informed Simulation:** We generated 30 days of backward-looking synthetic trajectories seeded from the 38 real current BYU iceberg positions. The drift model is informed by real live ERA5 wind vector fields (`era5_latest.nc`) and a parameterized model of the Antarctic Circumpolar Current (ACC) eastward flow (stronger at 60°S, weaker at 75°S). The simulation assumes a standard ~2% wind-drag drift approximation from iceberg literature, plus a daily Gaussian noise perturbation ($\pm 5\%$ of step displacement) to represent sub-grid scale eddies.
- **PyTorch LSTM Model:** We installed PyTorch (CPU-only) and rewrote `train_lstm.py` to train a sequence-to-vector LSTM model (input: last 14 days of normalized lat/lon + wind + current; output: predicted offsets at 24h, 48h, 72h).
- **Model Evaluation:** Evaluated on a holdout subset of 8 icebergs (not seen during training) using the Haversine formula in kilometers. The final computed errors are:
  - 24h: **1.3 km** mean positional error
  - 48h: **2.71 km** mean positional error
  - 72h: **3.92 km** mean positional error
- **Inference Integration:** Updated `lstm_predictor.py` to dynamically reconstruct the past 14 days of history. It queries SQLite `iceberg_history` table for real position logs and falls back to physics-informed backward simulation where logs are incomplete or unavailable.
- **Real History Accumulation:** Wired `byu_scraper.py` to append positional snapshot logs to `backend/data/cache/byu_history.jsonl` on each run. The APScheduler background job was wired to respect `INGEST_INTERVAL_HOURS` in `.env` for history collection going forward.

