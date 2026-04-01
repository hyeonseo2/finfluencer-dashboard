from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.models import Channel, ChannelSyncState, Video
from app.services.ingestion.rss_poller import parse_feed


def process_channel_feed(db: Session, channel: Channel) -> dict:
    state = db.query(ChannelSyncState).filter(ChannelSyncState.channel_id == channel.id).first()
    if not state:
        state = ChannelSyncState(channel_id=channel.id)
        db.add(state)
        db.commit()
        db.refresh(state)

    etag = None
    modified = None

    entries, new_etag, new_modified = parse_feed(channel.channel_id, etag=etag, modified=modified)

    new_count = 0
    for entry in entries:
        exists = db.query(Video).filter(Video.video_id == entry["video_id"]).first()
        if exists:
            continue
        from app.services.ingestion.pipeline import upsert_video_from_feed

        upsert_video_from_feed(db, channel, entry)
        new_count += 1

    state.last_polled_at = datetime.now(timezone.utc)
    if entries:
        state.last_success_at = datetime.now(timezone.utc)
        if entries[0].get("published_at"):
            state.last_feed_published_at = entries[0]["published_at"]
        state.last_error = None
        state.consecutive_failures = 0
    else:
        state.consecutive_failures = state.consecutive_failures + 1

    db.add(state)
    db.commit()
    return {
        "channel_id": channel.channel_id,
        "channel_id_db": channel.id,
        "entries": len(entries),
        "new_count": new_count,
        "etag": new_etag,
        "modified": new_modified,
    }
