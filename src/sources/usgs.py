import requests
from datetime import datetime, timezone

from src.config import APAC_BBOX, MIN_MAGNITUDE, SOURCES


def _in_apac(lon: float, lat: float) -> bool:
    b = APAC_BBOX
    return b["lat_min"] <= lat <= b["lat_max"] and b["lon_min"] <= lon <= b["lon_max"]


def fetch() -> list[dict]:
    resp = requests.get(SOURCES["usgs"], timeout=30)
    resp.raise_for_status()
    events = []
    for f in resp.json()["features"]:
        p = f["properties"]
        lon, lat, _ = f["geometry"]["coordinates"]
        mag = p.get("mag") or 0.0
        if mag < MIN_MAGNITUDE or not _in_apac(lon, lat):
            continue
        if mag >= 6.5:
            severity = "red"
        elif mag >= 5.5:
            severity = "orange"
        else:
            severity = "green"
        events.append({
            "source": "usgs",
            "event_id": f["id"],
            "event_type": "earthquake",
            "title": p.get("title", ""),
            "lat": lat,
            "lon": lon,
            "severity": severity,
            "magnitude": mag,
            "country": None,
            "occurred_at": datetime.fromtimestamp(
                p["time"] / 1000, tz=timezone.utc
            ).isoformat(),
            "url": p.get("url", ""),
        })
    return events
