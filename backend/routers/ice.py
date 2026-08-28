from fastapi import APIRouter, Query

from ml.icenet_runner import forecast_day

router = APIRouter()


@router.get("/forecast")
def forecast(day: int = Query(1, ge=1, le=7)):
    return forecast_day(day)
