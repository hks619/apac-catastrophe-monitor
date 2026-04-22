import feedparser
from datetime import datetime, timezone

from src.config import APAC_BBOX, SOURCES


def _in_apac(lon: float, lat: float) -> bool:
    b = APAC_BBOX
    return b["lat_min"] <= lat <= b["lat_max"] and b["lon_min"] <= lon <= b["lon_max"]


def _parse_coords(entry) -> tuple[float | None, float | None]:
    # feedparser maps geo:lat/geo:long namespace tags to these attributes
    lat = getattr(entry, "geo_lat", None)
    lon = getattr(entry, "geo_long", None)
    if lat is not None and lon is not None:
        return float(lat), float(lon)
    # georss:point fallback: "lat lon"
    point = getattr(entry, "georss_point", None)
    if point:
        parts = point.split()
        if len(parts) == 2:
            return float(parts[0]), float(parts[1])
    return None, None


def fetch() -> list[dict]:
    feed = feedparser.parse(SOURCES["gdacs"])
    events = []
    for entry in feed.entries:
        lat, lon = _parse_coords(entry)
        if lat is None or not _in_apac(lon, lat):
            continue

        event_id = str(
            getattr(entry, "gdacs_eventid", None)
            or getattr(entry, "id", None)
            or entry.get("link", "")
        )
        severity = (getattr(entry, "gdacs_alertlevel", "") or "green").lower()
        event_type = (getattr(entry, "gdacs_eventtype", "") or "unknown").lower()
        country = getattr(entry, "gdacs_country", None)

        occurred_at = None
        if entry.get("published_parsed"):
            occurred_at = datetime(
                *entry.published_parsed[:6], tzinfo=timezone.utc
            ).isoformat()

        events.append({
            "source": "gdacs",
            "event_id": event_id,
            "event_type": event_type,
            "title": entry.get("title", ""),
            "lat": lat,
            "lon": lon,
            "severity": severity,
            "magnitude": None,
            "country": country,
            "occurred_at": occurred_at,
            "url": entry.get("link", ""),
        })
    return events
