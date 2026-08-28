"""Scrape current Antarctic iceberg positions from BYU SCP (no auth)."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path

import httpx
from bs4 import BeautifulSoup

BYU_URL = "https://www.scp.byu.edu/current_icebergs.html"
SAMPLE_PATH = Path(__file__).parent / "samples" / "byu_icebergs_sample.json"
CACHE_PATH = Path(__file__).parent / "cache" / "byu_icebergs.json"

_DMS = re.compile(
    r"^\s*(\d+)\s+(\d+)'?\s*([NSEW])\s*$",
    re.IGNORECASE,
)


def dms_to_decimal(text: str) -> float | None:
    cleaned = text.replace("\xa0", " ").strip()
    m = _DMS.match(cleaned)
    if not m:
        try:
            return float(cleaned)
        except ValueError:
            return None
    deg = int(m.group(1))
    minutes = int(m.group(2))
    hemi = m.group(3).upper()
    val = deg + minutes / 60.0
    if hemi in {"S", "W"}:
        val = -val
    return val


def parse_table(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "lxml")
    rows: list[dict] = []
    for tr in soup.find_all("tr"):
        cells = [c.get_text(" ", strip=True) for c in tr.find_all(["td", "th"])]
        if len(cells) < 3:
            continue
        name, lon_s, lat_s = cells[0], cells[1], cells[2]
        if name.lower().startswith("iceberg"):
            continue
        lat = dms_to_decimal(lat_s)
        lon = dms_to_decimal(lon_s)
        if lat is None or lon is None:
            continue
        if not (-90 <= lat <= -50):
            continue
        doy = cells[3] if len(cells) > 3 else None
        rows.append(
            {
                "name": name.upper().replace(" ", ""),
                "lat": round(lat, 4),
                "lon": round(lon, 4),
                "doy": doy,
                "source": "BYU/NIC",
            }
        )
    return rows


def fetch_live(timeout: float = 30.0) -> tuple[list[dict], str]:
    headers = {"User-Agent": "POLARIS/0.1 (SIH PS26059 research; educational)"}
    with httpx.Client(timeout=timeout, follow_redirects=True, headers=headers) as client:
        r = client.get(BYU_URL)
        r.raise_for_status()
        icebergs = parse_table(r.text)
        if not icebergs:
            raise RuntimeError("Parsed 0 icebergs from BYU HTML")
        return icebergs, r.text


def load_sample() -> list[dict]:
    if SAMPLE_PATH.exists():
        return json.loads(SAMPLE_PATH.read_text(encoding="utf-8"))
    return []


def save_cache(icebergs: list[dict], live: bool) -> Path:
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "live": live,
        "count": len(icebergs),
        "icebergs": icebergs,
    }
    CACHE_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    SAMPLE_PATH.parent.mkdir(parents=True, exist_ok=True)
    if live:
        SAMPLE_PATH.write_text(json.dumps(icebergs, indent=2), encoding="utf-8")
    return CACHE_PATH


def run(force_sample: bool = False) -> dict:
    error = None
    live = False
    if force_sample:
        icebergs = load_sample()
        error = "forced sample"
    else:
        try:
            icebergs, _ = fetch_live()
            live = True
        except Exception as exc:  # noqa: BLE001 — fetcher must always return
            error = str(exc)
            icebergs = load_sample()
            live = False
    path = save_cache(icebergs, live)
    return {
        "status": "LIVE" if live else "FALLBACK",
        "count": len(icebergs),
        "error": error,
        "cache": str(path),
        "icebergs": icebergs,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample", action="store_true")
    args = parser.parse_args()
    result = run(force_sample=args.sample)
    print(json.dumps({k: result[k] for k in ("status", "count", "error", "cache")}, indent=2))
    print("names:", ", ".join(i["name"] for i in result["icebergs"][:12]), "...")


if __name__ == "__main__":
    main()
