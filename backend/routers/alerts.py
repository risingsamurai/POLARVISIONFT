from __future__ import annotations

import json
from math import asin, cos, radians, sin, sqrt
from pathlib import Path

from fastapi import APIRouter
from pydantic import BaseModel

from db.models import list_icebergs

router = APIRouter()
CFG = json.loads(
    (Path(__file__).resolve().parents[1] / "config" / "alerts.json").read_text(
        encoding="utf-8"
    )
)
ALERTS: list[dict] = []


class TelemetryIn(BaseModel):
    lat: float
    lon: float
    sog: float
    cog: float


def _nm(a: tuple[float, float], b: tuple[float, float]) -> float:
    r = 3440.065
    dlat = radians(b[0] - a[0])
    dlon = radians(b[1] - a[1])
    h = (
        sin(dlat / 2) ** 2
        + cos(radians(a[0])) * cos(radians(b[0])) * sin(dlon / 2) ** 2
    )
    return 2 * r * asin(min(1.0, sqrt(h)))


def classify(lat: float, lon: float) -> dict:
    nearest = None
    best = 1e9
    for b in list_icebergs():
        d = _nm((lat, lon), (b["lat"], b["lon"]))
        if d < best:
            best = d
            nearest = b
    name = nearest["name"] if nearest else "hazard"
    if best < CFG["criticalNm"]:
        return {
            "tier": "CRITICAL",
            "message": f"Vessel within {best:.1f} nm of {name}",
        }
    if best < CFG["warningNm"]:
        return {
            "tier": "WARNING",
            "message": f"Ice concentration / hazard {best:.1f} nm ahead",
        }
    return {"tier": "CLEAR", "message": "All hazards outside safe radius"}


@router.get("/api/alerts")
def alerts():
    return {"alerts": ALERTS[-50:], "thresholds": CFG}


@router.post("/api/alerts/evaluate")
def evaluate(body: TelemetryIn):
    alert = classify(body.lat, body.lon)
    ALERTS.append(alert)
    return alert
