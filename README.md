# APAC Catastrophe Monitor

Real-time multi-hazard event dashboard for reinsurance catastrophe risk analysis across the Asia-Pacific region.

## Architecture

```
Data Sources            Ingestion              Storage          Visualization
────────────            ─────────              ───────          ─────────────
USGS FDSN  ──────┐
GDACS RSS  ──────┤   src/ingest.py        data/events.db   src/dashboard.py
ReliefWeb  ──────┤   (orchestrator,   →   (SQLite,      →  (Streamlit —
NASA EONET ──────┘    fault-tolerant)      idempotent        map, KPIs,
                                           upserts)          charts, CSV)

GitHub Actions: cron every 3 h → python -m src.ingest → git commit data/events.db
```

| Source | Hazards | Filter |
|---|---|---|
| USGS | Earthquakes | APAC bbox + M ≥ 4.5 |
| GDACS | Multi-hazard (floods, cyclones, volcanoes…) | APAC bbox |
| ReliefWeb (UN OCHA) | All disaster types | ~50 APAC ISO3 codes |
| NASA EONET | Wildfires, storms, volcanoes | APAC bbox |

## Quick Start

```bash
git clone <repo-url>
cd apac-catastrophe-monitor

pip install -r requirements.txt

# Populate the database
python -m src.ingest

# Launch the dashboard
streamlit run src/dashboard.py
```

## Running Tests

```bash
pytest tests/
```

## Project Structure

```
apac-catastrophe-monitor/
├── README.md
├── requirements.txt
├── .gitignore
├── data/
│   └── events.db          # committed by CI after each ingestion run
├── src/
│   ├── config.py          # APAC bbox, ISO3 list, source URLs, thresholds
│   ├── storage.py         # SQLite schema + idempotent upsert
│   ├── ingest.py          # orchestrator (fault-tolerant per source)
│   ├── dashboard.py       # Streamlit app
│   └── sources/
│       ├── usgs.py        # USGS earthquake GeoJSON
│       ├── gdacs.py       # GDACS RSS multi-hazard feed
│       ├── reliefweb.py   # UN OCHA ReliefWeb disaster API
│       └── eonet.py       # NASA EONET satellite events
├── tests/
│   └── test_geo_filter.py # bbox + ISO3 sanity checks
└── .github/
    └── workflows/
        └── ingest.yml     # 3-hourly scheduled ingestion
```

## Extending with Claude Code

**Add a new data source**
> "Add `src/sources/pdc.py` that fetches from the Pacific Disaster Center API at `https://www.pdc.org/` and integrates it into `src/ingest.py` alongside the existing sources. Match the same event dict schema used by the other sources."

**Add Slack / email alerts for red-severity events**
> "Add `src/alerts.py` that checks for new red-severity events inserted in the last ingestion run and sends a Slack webhook message (SLACK_WEBHOOK_URL env var). Call it from `src/ingest.py` after the upsert loop."

**Country-level risk scoring**
> "Add a risk scoring module `src/risk.py` that aggregates event frequency and average severity per ISO3 country over the past 12 months, assigns a risk tier (low / medium / high / critical), and surfaces it as a choropleth map in `src/dashboard.py`."

**Historical backfill**
> "Extend `src/sources/usgs.py` to accept a `start_time` / `end_time` parameter using the USGS ComCat API (`https://earthquake.usgs.gov/fdsnws/event/1/`) instead of the rolling feed, and add a CLI flag `--backfill-days N` to `src/ingest.py`."

**Add Mapbox token for satellite tiles**
> "Read `MAPBOX_TOKEN` from an env var in `src/dashboard.py` and pass it to `pdk.Deck(api_keys={'mapbox': token})` so the map can use satellite-streets style."
