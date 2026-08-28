# POLARIS — Data Sources

Auth requirements, rate limits, fallback sample locations, and the **Data Reality Table** (source of truth for live vs cached).

## Fetchers

| Source | Fetcher | Auth | Rate limits | Sample / cache path |
|---|---|---|---|---|
| NSIDC (NOAA) | `backend/data/nsidc_fetcher.py` | None (Direct HTTPS) | None | `backend/data/samples/nsidc_sic_sample.json` |
| BYU/NIC | `backend/data/byu_scraper.py` | None | Polite 6h schedule | `backend/data/samples/byu_icebergs_sample.json` |
| ERA5 (CDS) | `backend/data/era5_fetcher.py` | `CDS_API_KEY` | **120 requests/day** | `backend/data/samples/era5_sample.json` |

## Data Reality Table

Updated 2026-08-28 after live scraper + local API verification.

| Source | Status right now | Last successful live fetch | Why (if fallback) |
|---|---|---|---|
| NSIDC | LIVE | 2026-08-28 (this session) | Successfully downloaded and parsed NOAA@NSIDC `G10016` V4 Southern Hemisphere daily NetCDF via direct HTTPS listing |
| BYU/NIC | LIVE | 2026-08-28 (this session) | Scraped `https://www.scp.byu.edu/current_icebergs.html`; **38** named icebergs including A76C, A81, A83. Rows in SQLite `icebergs` table = 38 |
| ERA5 | LIVE | 2026-08-28 (this session) | Successfully authenticated with `CDS_API_KEY`, downloaded Copernicus CDS NetCDF, and mapped coordinates using nearest neighbor xarray interpolation |

## Pipeline (this run)

Startup ingest in FastAPI lifespan: BYU scrape → SQLite `icebergs` + `iceberg_history` → NSIDC/ERA5 fallback grids → in-process cache. APScheduler interval job registered for 6 hours. Redis was not running (Docker not installed), so `redis_cache.py` kept an in-memory dict.

PostgreSQL+PostGIS is defined in `docker-compose.yml` but was **not** used in this session because `docker` is not on PATH. Local acceptance used SQLite `backend/polaris.db`.
