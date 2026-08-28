from fastapi import APIRouter
from pydantic import BaseModel

from db.models import list_icebergs
from ml.astar_router import three_routes

router = APIRouter()


class RouteRequest(BaseModel):
    start: list[float]
    destination: list[float]


@router.post("/")
def compute_route(body: RouteRequest):
    bergs = list_icebergs()
    routes = three_routes(body.start, body.destination, bergs)
    return {"status": "ok", "routes": routes}
