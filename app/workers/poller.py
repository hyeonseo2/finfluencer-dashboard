from __future__ import annotations

import logging
import time

from app.core.config import settings
from app.core.logging import init_logging
from app.db.base import SessionLocal
from app.services.ingestion.channel_ingest import process_channel_feed
from app.services.ingestion.job_queue import get_active_channels_for_poll

log = logging.getLogger("finfluencer.poller")


def poll_once() -> list[dict]:
    db = SessionLocal()
    out = []
    try:
        channels = get_active_channels_for_poll(db)
        for ch in channels:
            out.append(process_channel_feed(db, ch))
    finally:
        db.close()
    return out


def loop() -> None:
    init_logging()
    log.info("poller started")
    while True:
        try:
            stats = poll_once()
            log.info("poll_done", extra={"channels": len(stats), "stats": stats})
        except Exception:
            log.exception("poller_error")
        time.sleep(max(30, settings.poller_interval_seconds))


def main() -> None:
    loop()


if __name__ == "__main__":
    main()
