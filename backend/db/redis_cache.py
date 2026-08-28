"""In-process hot cache. Redis used when REDIS_URL is reachable."""

from __future__ import annotations

import json
import os
from typing import Any

_mem: dict[str, str] = {}


def _redis():
    url = os.getenv("REDIS_URL")
    if not url:
        return None
    try:
        import redis  # type: ignore

        client = redis.Redis.from_url(url, socket_connect_timeout=0.4)
        client.ping()
        return client
    except Exception:
        return None


def set_json(key: str, value: Any) -> None:
    blob = json.dumps(value)
    _mem[key] = blob
    r = _redis()
    if r is not None:
        r.set(key, blob, ex=3600)


def get_json(key: str) -> Any | None:
    r = _redis()
    if r is not None:
        raw = r.get(key)
        if raw:
            return json.loads(raw)
    raw = _mem.get(key)
    return json.loads(raw) if raw else None
