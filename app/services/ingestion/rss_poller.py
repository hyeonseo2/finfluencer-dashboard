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
    
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    if etag:
        headers["If-None-Match"] = etag
    if modified:
        headers["If-Modified-Since"] = modified
        
    import requests
    try:
        r = requests.get(url, headers=headers, timeout=15)
        # Handle 304 Not Modified
        if r.status_code == 304:
            parsed = feedparser.parse("")
            parsed.status = 304
        else:
            parsed = feedparser.parse(r.content)
            parsed.etag = r.headers.get("etag")
            parsed.modified = r.headers.get("last-modified")
    except Exception:
        parsed = feedparser.parse(url, etag=etag, modified=modified)

    if getattr(parsed, "bozo", False) and r.status_code != 304:
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
