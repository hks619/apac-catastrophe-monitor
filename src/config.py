from pathlib import Path

# SQLite database location
DB_PATH = Path(__file__).parent.parent / "data" / "events.db"

# Minimum earthquake magnitude to ingest
MIN_MAGNITUDE = 4.5

# Data source URLs (ReliefWeb owns its own URL; see src/sources/reliefweb.py)
SOURCES = {
    "usgs": "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/4.5_month.geojson",
    "gdacs": "https://www.gdacs.org/xml/rss.xml",
    "eonet": "https://eonet.gsfc.nasa.gov/api/v3/events",
}
