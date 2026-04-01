from __future__ import annotations

import json
import pathlib

from sqlalchemy.orm import Session

from app.db.base import SessionLocal
from app.models.models import Channel, ChannelSyncState
from app.services.youtube.client import resolve_channel_by_handle


def main(seed_path: str = "sample_seed_channels.json") -> None:
    db: Session = SessionLocal()
    with open(seed_path, encoding="utf-8") as f:
        rows = json.load(f)

    for r in rows:
        handle = r.get("handle")
        ch_id = r.get("channel_id")
        if not ch_id and handle:
            resolved = resolve_channel_by_handle(handle)
            ch_id = resolved["channel_id"]
            display_name = resolved["display_name"]
        else:
            display_name = r["display_name"]

        existing = db.query(Channel).filter(Channel.channel_id == ch_id).first()
        if existing:
            continue

        ch = Channel(
            channel_id=ch_id,
            handle=handle,
            display_name=display_name,
            category_primary=r["category_primary"],
            country=r.get("country", "KR"),
            language=r.get("language", "ko"),
            is_interview_heavy=r.get("is_interview_heavy", False),
            active=r.get("active", True),
        )
        db.add(ch)
        db.flush()
        db.add(ChannelSyncState(channel_id=ch.id))
    db.commit()
    print(f"seeded: {len(rows)}")


if __name__ == "__main__":
    main()
