"""
One-time backfill script.

Usage:
    python -m src.backfill            # 1 year of USGS earthquakes (default)
    python -m src.backfill --years 2  # 2 years
"""

import argparse
import logging
from datetime import datetime, timedelta, timezone

from src.sources.usgs import fetch_historical
from src.storage import get_conn, init_db, upsert_event

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
log = logging.getLogger(__name__)

_CHUNK_DAYS = 30


def backfill_usgs(years: int = 1):
    now = datetime.now(timezone.utc)
    start = now - timedelta(days=365 * years)
    current = start
    total = 0

    with get_conn() as conn:
        while current < now:
            chunk_end = min(current + timedelta(days=_CHUNK_DAYS), now)
            try:
                events = fetch_historical(current, chunk_end)
                for ev in events:
                    upsert_event(conn, ev)
                total += len(events)
                log.info(
                    "%s → %s: %d events (running total: %d)",
                    current.date(), chunk_end.date(), len(events), total,
                )
            except Exception as exc:
                log.error("%s → %s: failed — %s", current.date(), chunk_end.date(), exc)
            current = chunk_end

    log.info("USGS backfill complete — %d events ingested", total)


def main():
    parser = argparse.ArgumentParser(description="Backfill historical global earthquake data")
    parser.add_argument("--years", type=int, default=1, help="Years of history to fetch (default: 1)")
    args = parser.parse_args()

    init_db()
    log.info("Backfilling %d year(s) of USGS M%.1f+ earthquakes globally…", args.years, 4.5)
    backfill_usgs(years=args.years)


if __name__ == "__main__":
    main()
