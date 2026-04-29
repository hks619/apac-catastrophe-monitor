import logging
import os

import requests

from src.config import APAC_ISO3

log = logging.getLogger(__name__)

# ReliefWeb v1 was decommissioned; v2 requires a registered appname.
# Register at https://apidoc.reliefweb.int/parameters#appname
# Set RELIEFWEB_APPNAME env var (or accept rate-limited anonymous access).
_BASE_URL = "https://api.reliefweb.int/v2/disasters"


def fetch() -> list[dict]:
    appname = os.environ.get("RELIEFWEB_APPNAME", "")
    if not appname:
        log.warning(
            "RELIEFWEB_APPNAME not set — skipping ReliefWeb. "
            "Register at https://apidoc.reliefweb.int/parameters#appname"
        )
        return []

    payload = {
        "filter": {
            "operator": "AND",
            "conditions": [
                {"field": "status", "value": ["ongoing", "alert"]},
                {"field": "primary_country.iso3", "value": list(APAC_ISO3)},
            ],
        },
        "fields": {
            "include": ["id", "name", "type", "status", "primary_country", "date", "url"],
        },
        "limit": 200,
        "sort": ["date.created:desc"],
    }
    resp = requests.post(f"{_BASE_URL}?appname={appname}", json=payload, timeout=30)
    resp.raise_for_status()

    events = []
    for item in resp.json().get("data", []):
        f = item.get("fields", {})

        country_info = f.get("primary_country", {})
        country = country_info.get("iso3") if isinstance(country_info, dict) else None

        types = f.get("type", [])
        if types and isinstance(types, list):
            first = types[0]
            event_type = (first.get("name", "") if isinstance(first, dict) else str(first)).lower()
        else:
            event_type = "disaster"

        date_info = f.get("date", {})
        occurred_at = date_info.get("event") or date_info.get("created")

        events.append({
            "source": "reliefweb",
            "event_id": str(item["id"]),
            "event_type": event_type,
            "title": f.get("name", ""),
            "lat": None,
            "lon": None,
            "severity": None,
            "magnitude": None,
            "country": country,
            "occurred_at": occurred_at,
            "url": f.get("url", ""),
        })
    return events
