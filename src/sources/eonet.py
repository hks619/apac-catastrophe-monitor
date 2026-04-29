import requests

from src.config import SOURCES

_CATEGORY_MAP = {
    "wildfires": "wildfire",
    "volcanoes": "volcano",
    "severeStorms": "storm",
    "floods": "flood",
    "earthquakes": "earthquake",
    "seaLakeIce": "ice",
    "drought": "drought",
    "dustHaze": "dust",
    "manmade": "manmade",
    "snow": "snow",
    "tempExtremes": "temperature",
}


def fetch() -> list[dict]:
    resp = requests.get(
        SOURCES["eonet"],
        params={"status": "all", "limit": 500, "days": 90},
        timeout=30,
    )
    resp.raise_for_status()

    events = []
    for ev in resp.json().get("events", []):
        geometries = ev.get("geometry", [])
        if not geometries:
            continue
        point_geom = next(
            (g for g in reversed(geometries) if g.get("type") == "Point"), None
        )
        if point_geom is None:
            continue
        lon, lat = point_geom["coordinates"]

        categories = ev.get("categories", [])
        cat_id = categories[0].get("id", "") if categories else ""
        event_type = _CATEGORY_MAP.get(cat_id, cat_id.lower() or "unknown")

        sources = ev.get("sources", [])
        url = sources[0].get("url", "") if sources else ""

        events.append({
            "source": "eonet",
            "event_id": ev["id"],
            "event_type": event_type,
            "title": ev.get("title", ""),
            "lat": lat,
            "lon": lon,
            "severity": None,
            "magnitude": None,
            "country": None,
            "occurred_at": point_geom.get("date"),
            "url": url,
        })
    return events
