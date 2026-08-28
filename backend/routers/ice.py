import json
from fastapi import APIRouter, Query

from ml.icenet_runner import forecast_day
from data.nsidc_fetcher import CACHE_PATH, synthetic_grid

router = APIRouter()


@router.get("/forecast")
def forecast(day: int = Query(1, ge=1, le=7)):
    return forecast_day(day)


@router.get("/current")
def current():
    if CACHE_PATH.exists():
        try:
            base = json.loads(CACHE_PATH.read_text(encoding="utf-8"))
            cells = base.get("cells") or synthetic_grid()["cells"]
        except Exception:
            cells = synthetic_grid()["cells"]
    else:
        cells = synthetic_grid()["cells"]
    return {
        "model": "live_nsidc",
        "grid": cells,
    }

