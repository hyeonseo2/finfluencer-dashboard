from __future__ import annotations

from sqlalchemy.orm import Session

from app.db.base import SessionLocal
from app.models.models import Channel
from app.services.ingestion.channel_ingest import process_channel_feed


def main(channel_id: str) -> None:
    db: Session = SessionLocal()
    ch = db.query(Channel).filter(Channel.channel_id == channel_id).first()
    if not ch:
        ch = db.query(Channel).filter(Channel.id == int(channel_id)).first()
    if not ch:
        raise SystemExit("channel not found")
    out = process_channel_feed(db, ch)
    print(out)


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        raise SystemExit("usage: python backfill_channel.py <channel_id>")
    main(sys.argv[1])
