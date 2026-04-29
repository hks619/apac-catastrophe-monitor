from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "events.db"

MIN_MAGNITUDE = 4.5

REGIONS = {
    "Global": {
        "bbox": None,
        "center": {"lat": 20, "lon": 0, "zoom": 1},
    },
    "APAC": {
        "bbox": {"lat_min": -50.0, "lat_max": 55.0, "lon_min": 60.0, "lon_max": 180.0},
        "center": {"lat": 10, "lon": 115, "zoom": 2},
    },
    "Europe": {
        "bbox": {"lat_min": 34.0, "lat_max": 72.0, "lon_min": -25.0, "lon_max": 45.0},
        "center": {"lat": 50, "lon": 10, "zoom": 3},
    },
    "Africa": {
        "bbox": {"lat_min": -35.0, "lat_max": 38.0, "lon_min": -20.0, "lon_max": 52.0},
        "center": {"lat": 5, "lon": 20, "zoom": 3},
    },
    "North America": {
        "bbox": {"lat_min": 15.0, "lat_max": 72.0, "lon_min": -170.0, "lon_max": -50.0},
        "center": {"lat": 45, "lon": -100, "zoom": 2},
    },
    "South America": {
        "bbox": {"lat_min": -56.0, "lat_max": 13.0, "lon_min": -82.0, "lon_max": -34.0},
        "center": {"lat": -15, "lon": -60, "zoom": 2},
    },
    "Antarctica": {
        "bbox": {"lat_min": -90.0, "lat_max": -60.0, "lon_min": -180.0, "lon_max": 180.0},
        "center": {"lat": -80, "lon": 0, "zoom": 2},
    },
}

# Data source URLs (ReliefWeb owns its own URL; see src/sources/reliefweb.py)
SOURCES = {
    "usgs":  "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/4.5_month.geojson",
    "gdacs": "https://www.gdacs.org/xml/rss.xml",
    "eonet": "https://eonet.gsfc.nasa.gov/api/v3/events",
}
