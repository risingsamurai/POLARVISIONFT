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

scheduler = BackgroundScheduler()


def ingest_all() -> None:
    init_db()
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
    scheduler.add_job(ingest_all, "interval", hours=6, id="ingest")
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
