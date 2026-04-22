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

## Extending

**Add a new data source** — create a new module under `src/sources/` that returns a list of event dicts matching the schema in `src/storage.py`, then register it in the `_SOURCES` list in `src/ingest.py`.

**Add Slack / email alerts** — add `src/alerts.py` that queries for new red-severity events after each ingestion run and sends a webhook message. Call it from `src/ingest.py` after the upsert loop.

**Country-level risk scoring** — add `src/risk.py` that aggregates event frequency and severity per ISO3 country, assigns a risk tier (low / medium / high / critical), and surfaces it as a choropleth in `src/dashboard.py`.

**Historical backfill** — extend `src/sources/usgs.py` to use the USGS ComCat API with `start_time` / `end_time` parameters and add a `--backfill-days N` CLI flag to `src/ingest.py`.
