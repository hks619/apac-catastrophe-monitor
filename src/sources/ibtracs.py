import io
import logging
from datetime import datetime, timedelta, timezone

import pandas as pd
import requests

log = logging.getLogger(__name__)

_URL = (
    "https://www.ncei.noaa.gov/data/international-best-track-archive-for-climate-stewardship-ibtracs"
    "/v04r01/access/csv/ibtracs.last3years.list.v04r01.csv"
)

# APAC basins: Western Pacific, North Indian, South Indian, South Pacific
_APAC_BASINS = {"WP", "NI", "SI", "SP"}


def _sshs_to_severity(sshs) -> str:
    try:
        cat = int(float(sshs))
    except (ValueError, TypeError):
        return "green"
    if cat >= 3:
        return "red"
    if cat >= 1:
        return "orange"
    return "green"


def fetch() -> list[dict]:
    resp = requests.get(_URL, timeout=90)
    resp.raise_for_status()

    # Row 0 = column headers, row 1 = units — skip the units row
    df = pd.read_csv(
        io.StringIO(resp.text),
        skiprows=[1],
        low_memory=False,
        na_values=[" "],
    )

    df = df[df["BASIN"].isin(_APAC_BASINS)].copy()

    df["ISO_TIME"] = pd.to_datetime(df["ISO_TIME"], utc=True, errors="coerce")
    cutoff = datetime.now(timezone.utc) - timedelta(days=365)
    df = df[df["ISO_TIME"] >= cutoff].dropna(subset=["ISO_TIME", "LAT", "LON"])

    events = []
    for _, row in df.iterrows():
        try:
            lat = float(row["LAT"])
            lon = float(row["LON"])
        except (ValueError, TypeError):
            continue

        sid = str(row["SID"]).strip()
        iso_time = row["ISO_TIME"].isoformat()

        name = str(row.get("NAME", "")).strip()
        if not name or name.upper() in ("NOT_NAMED", "NAN", ""):
            name = f"Storm {sid[-6:]}"

        try:
            wind = float(row.get("USA_WIND") or row.get("WMO_WIND") or 0)
            wind = wind if wind > 0 else None
        except (ValueError, TypeError):
            wind = None

        severity = _sshs_to_severity(row.get("USA_SSHS"))

        events.append({
            "source": "ibtracs",
            "event_id": f"{sid}|{iso_time}",
            "event_type": "cyclone",
            "title": f"Tropical Cyclone {name}",
            "lat": lat,
            "lon": lon,
            "severity": severity,
            "magnitude": wind,   # max wind speed in knots
            "country": None,
            "occurred_at": iso_time,
            "url": "https://www.ncdc.noaa.gov/ibtracs/",
        })

    return events
