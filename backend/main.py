from contextlib import asynccontextmanager

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from data.byu_scraper import run as scrape_byu
from data.era5_fetcher import run as fetch_era5
from data.nsidc_fetcher import run as fetch_nsidc
from db.models import iceberg_count, init_db, upsert_icebergs
from db.redis_cache import set_json
from routers import alerts, health, ice, icebergs, routing, telemetry

import os
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv(), override=True)

scheduler = BackgroundScheduler()


def ingest_all() -> None:
    init_db()
    if os.getenv("OFFLINE_STARTUP", "").lower() == "true":
        import json
        from pathlib import Path
        
        # Load BYU Cache
        byu_cache = Path(__file__).parent / "data" / "cache" / "byu_icebergs.json"
        if byu_cache.exists():
            byu = json.loads(byu_cache.read_text(encoding="utf-8"))
        else:
            byu = {"status": "FALLBACK", "icebergs": []}
            
        # Load NSIDC Cache
        nsidc_cache = Path(__file__).parent / "data" / "cache" / "nsidc_sic.json"
        if nsidc_cache.exists():
            nsidc = json.loads(nsidc_cache.read_text(encoding="utf-8"))
        else:
            nsidc = {"status": "FALLBACK"}
            
        # Load ERA5 Cache
        era5_cache = Path(__file__).parent / "data" / "cache" / "era5.json"
        if era5_cache.exists():
            era5 = json.loads(era5_cache.read_text(encoding="utf-8"))
        else:
            era5 = {"status": "FALLBACK"}
            
        upsert_icebergs(byu.get("icebergs", []), live=byu.get("live", False))
        set_json(
            "data_reality",
            {
                "byu": {
                    "status": "FALLBACK",
                    "count": len(byu.get("icebergs", [])),
                    "error": "Fallback: OFFLINE_STARTUP mode, live fetch skipped",
                },
                "nsidc": {
                    "status": "FALLBACK",
                    "fetched_at": nsidc.get("fetched_at"),
                    "error": "Fallback: OFFLINE_STARTUP mode, live fetch skipped",
                },
                "era5": {
                    "status": "FALLBACK",
                    "fetched_at": era5.get("fetched_at"),
                    "error": "Fallback: OFFLINE_STARTUP mode, live fetch skipped",
                },
            },
        )
        return

    byu = scrape_byu()
    upsert_icebergs(byu["icebergs"], live=byu["status"] == "LIVE")
    nsidc = fetch_nsidc()
    era5 = fetch_era5()
    set_json(
        "data_reality",
        {
            "byu": {"status": byu["status"], "count": byu["count"], "error": byu.get("error")},
            "nsidc": nsidc,
            "era5": era5,
        },
    )


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    ingest_all()
    
    interval_hours = int(os.getenv("INGEST_INTERVAL_HOURS", 6))
    scheduler.add_job(ingest_all, "interval", hours=interval_hours, id="ingest")
    scheduler.start()
    yield
    scheduler.shutdown(wait=False)


app = FastAPI(title="POLARIS API", version="0.2.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(alerts.router, tags=["alerts"])
app.include_router(health.router)
app.include_router(ice.router, prefix="/api/ice", tags=["ice"])
app.include_router(icebergs.router, prefix="/api/icebergs", tags=["icebergs"])
app.include_router(routing.router, prefix="/api/route", tags=["routing"])
app.include_router(telemetry.router, tags=["telemetry"])


@app.get("/")
def root():
    return {"service": "POLARIS", "status": "ok", "icebergs": iceberg_count()}
