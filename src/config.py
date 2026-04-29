from pathlib import Path

# SQLite database location
DB_PATH = Path(__file__).parent.parent / "data" / "events.db"

# APAC geographic bounding box
APAC_BBOX = {
    "lat_min": -50.0,
    "lat_max": 55.0,
    "lon_min": 60.0,
    "lon_max": 180.0,
}

# Minimum earthquake magnitude to ingest
MIN_MAGNITUDE = 4.5

# APAC ISO3 country codes
APAC_ISO3 = {
    "AFG", "ARM", "AUS", "AZE", "BGD", "BRN", "BTN", "CHN",
    "FJI", "FSM", "GEO", "HKG", "IDN", "IND", "JPN", "KAZ",
    "KGZ", "KHM", "KIR", "KOR", "LAO", "LKA", "MAC", "MDV",
    "MHL", "MMR", "MNG", "MYS", "NPL", "NRU", "NZL", "PAK",
    "PHL", "PLW", "PNG", "PRK", "SGP", "SLB", "THA", "TJK",
    "TKM", "TLS", "TON", "TUV", "TWN", "UZB", "VNM", "VUT",
    "WSM",
}

# Data source URLs (ReliefWeb owns its own URL; see src/sources/reliefweb.py)
SOURCES = {
    "usgs": "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/4.5_month.geojson",
    "gdacs": "https://www.gdacs.org/xml/rss.xml",
    "eonet": "https://eonet.gsfc.nasa.gov/api/v3/events",
}
