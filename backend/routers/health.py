from fastapi import APIRouter
from db.redis_cache import get_json

router = APIRouter()


@router.get("/health")
def health():
    return {"status": "ok", "service": "polaris-backend"}


@router.get("/api/status")
def api_status():
    reality = get_json("data_reality")
    if not reality:
        reality = {
            "byu": {"status": "FALLBACK", "count": 0, "error": None},
            "nsidc": {"status": "FALLBACK", "live": False, "error": None},
            "era5": {"status": "FALLBACK", "live": False, "error": None},
        }
    return reality
