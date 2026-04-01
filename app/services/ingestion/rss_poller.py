from __future__ import annotations

import datetime as dt
from typing import Any

import feedparser


def extract_video_id(entry: Any) -> str | None:
    yt_id = None
    if hasattr(entry, "yt_videoid"):
        yt_id = getattr(entry, "yt_videoid")
    elif getattr(entry, "link", None):
        # fallback parse .../watch?v=VIDEOID
        import re

        m = re.search(r"v=([A-Za-z0-9_-]{6,})", entry.link)
        if m:
            yt_id = m.group(1)
    return yt_id


def parse_published(entry) -> dt.datetime | None:
    if getattr(entry, "published_parsed", None):
        t = dt.datetime(*entry.published_parsed[:6], tzinfo=dt.timezone.utc)
        return t
    return None


def parse_feed(channel_id: str, etag: str | None = None, modified: str | None = None) -> tuple[list[dict], str | None, str | None]:
    url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
    parsed = feedparser.parse(url, etag=etag, modified=modified)
    if getattr(parsed, "bozo", False):
        raise RuntimeError(getattr(parsed, "bozo_exception", "RSS parse error"))

    entries = []
    for entry in parsed.entries:
        vid = extract_video_id(entry)
        if not vid:
            continue
        entries.append(
            {
                "video_id": vid,
                "channel_id_key": channel_id,
                "title": getattr(entry, "title", None),
                "published_at": parse_published(entry),
                "source_url": getattr(entry, "link", None),
            }
        )
    return entries, getattr(parsed, "etag", None), getattr(parsed, "modified", None)
