import logging

from src.sources import eonet, gdacs, reliefweb, usgs
from src.storage import get_conn, init_db, upsert_event

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)
log = logging.getLogger(__name__)

_SOURCES = [
    ("usgs", usgs.fetch),
    ("gdacs", gdacs.fetch),
    ("reliefweb", reliefweb.fetch),
    ("eonet", eonet.fetch),
]


def run():
    init_db()
    with get_conn() as conn:
        for name, fetch_fn in _SOURCES:
            try:
                events = fetch_fn()
                for ev in events:
                    upsert_event(conn, ev)
                log.info("%s: ingested %d events", name, len(events))
            except Exception as exc:
                log.error("%s: failed — %s", name, exc)


if __name__ == "__main__":
    run()
