import requests
from datetime import datetime, timezone

from src.config import MIN_MAGNITUDE, SOURCES

_COMCAT_URL = "https://earthquake.usgs.gov/fdsnws/event/1/query"


def _parse_features(features: list) -> list[dict]:
    events = []
    for f in features:
        p = f["properties"]
        lon, lat, _ = f["geometry"]["coordinates"]
        mag = p.get("mag") or 0.0
        if mag < MIN_MAGNITUDE:
            continue
        if mag >= 6.5:
            severity = "red"
        elif mag >= 5.5:
            severity = "orange"
        else:
            severity = "green"
        events.append({
            "source":     "usgs",
            "event_id":   f["id"],
            "event_type": "earthquake",
            "title":      p.get("title", ""),
            "lat":        lat,
            "lon":        lon,
            "severity":   severity,
            "magnitude":  mag,
            "country":    None,
            "occurred_at": datetime.fromtimestamp(
                p["time"] / 1000, tz=timezone.utc
            ).isoformat(),
            "url": p.get("url", ""),
        })
    return events


def fetch() -> list[dict]:
    resp = requests.get(SOURCES["usgs"], timeout=30)
    resp.raise_for_status()
    return _parse_features(resp.json()["features"])


def fetch_historical(start: datetime, end: datetime) -> list[dict]:
    """Fetch from the USGS ComCat API for an arbitrary date range (global)."""
    resp = requests.get(
        _COMCAT_URL,
        params={
            "format":       "geojson",
            "starttime":    start.strftime("%Y-%m-%d"),
            "endtime":      end.strftime("%Y-%m-%d"),
            "minmagnitude": MIN_MAGNITUDE,
            "limit":        20_000,
            "orderby":      "time",
        },
        timeout=60,
    )
    resp.raise_for_status()
    return _parse_features(resp.json()["features"])
