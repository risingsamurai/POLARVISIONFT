from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()
clients: set[WebSocket] = set()


async def broadcast(payload: dict) -> None:
    dead = []
    for ws in clients:
        try:
            await ws.send_json(payload)
        except Exception:
            dead.append(ws)
    for ws in dead:
        clients.discard(ws)


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    clients.add(websocket)
    await websocket.send_json(
        {"type": "hello", "service": "polaris", "ts": datetime.now(timezone.utc).isoformat()}
    )
    try:
        while True:
            raw = await websocket.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                msg = {"type": "text", "payload": raw}
            if msg.get("type") == "telemetry":
                await broadcast({"type": "telemetry", "data": msg.get("data")})
            else:
                await websocket.send_json({"type": "ack", "echo": msg})
    except WebSocketDisconnect:
        clients.discard(websocket)
