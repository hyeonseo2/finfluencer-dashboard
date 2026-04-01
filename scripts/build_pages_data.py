#!/usr/bin/env python3
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
import re

import feedparser
import requests

ROOT = Path(__file__).resolve().parents[1]
SEED_PATH = ROOT / "sample_seed_channels.json"
OUT_PATH = ROOT / "docs" / "data" / "latest.json"

TOPIC_RULES = {
    "stocks": [r"주식", r"증시", r"코스피", r"코스닥", r"s&p", r"나스닥", r"다우", r"삼성전자"],
    "commodities": [r"원자재", r"금\b", r"은\b", r"구리", r"유가", r"wti", r"브렌트"],
    "crypto": [r"비트코인", r"이더리움", r"코인", r"암호화폐", r"btc", r"eth"],
    "etf": [r"etf"],
    "fx": [r"환율", r"달러", r"원화", r"엔화", r"외환", r"fx"],
    "interest_rate": [r"금리", r"기준금리", r"fed", r"fomc", r"연준"],
    "macro": [r"경기", r"거시", r"침체", r"성장률", r"cpi", r"pce", r"실업"],
    "policy": [r"정책", r"재정", r"관세", r"규제", r"법안"],
    "real_estate": [r"부동산", r"아파트", r"전세", r"매매", r"청약"],
    "bonds": [r"채권", r"국채", r"회사채", r"채권금리"],
}


def _handle_url(handle: str) -> str:
    h = handle or ""
    if not h.startswith("@"):
        h = f"@{h}"
    return f"https://www.youtube.com/{h}"


def resolve_channel_meta(handle: str) -> tuple[str | None, str | None]:
    """Return (channel_id, avatar_url) from handle page/oEmbed when possible."""
    if not handle:
        return None, None

    url = _handle_url(handle)

    # 1) oEmbed is often the most reliable on CI
    try:
        r = requests.get(
            "https://www.youtube.com/oembed",
            params={"url": url, "format": "json"},
            timeout=15,
            headers={"User-Agent": "Mozilla/5.0"},
        )
        if r.ok:
            j = r.json()
            author_url = str(j.get("author_url") or "")
            m = re.search(r"/channel/(UC[\w-]{20,})", author_url)
            cid = m.group(1) if m else None
            avatar = j.get("thumbnail_url")
            if cid:
                return cid, avatar
    except Exception:
        pass

    # 2) Handle page fallback
    try:
        r = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        if not r.ok:
            return None, None
        text = r.text
        m = re.search(r'"channelId"\s*:\s*"(UC[\w-]{20,})"', text)
        cid = m.group(1) if m else None
        img = re.search(r'<meta[^>]+property="og:image"[^>]+content="([^"]+)"', text)
        avatar = img.group(1) if img else None
        return cid, avatar
    except Exception:
        return None, None


def infer_topics(title: str) -> list[str]:
    text = (title or "").lower()
    out: list[str] = []
    for topic, patterns in TOPIC_RULES.items():
        if any(re.search(p, text, flags=re.IGNORECASE) for p in patterns):
            out.append(topic)
    return out or ["macro"]


def parse_feed(channel_id: str) -> list[dict]:
    url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
    feed = feedparser.parse(url)
    rows: list[dict] = []

    for e in feed.entries[:12]:
        video_id = getattr(e, "yt_videoid", None) or (e.get("id", "").split(":")[-1] if e.get("id") else None)
        if not video_id:
            continue

        title = e.get("title", "")
        link = e.get("link") or f"https://www.youtube.com/watch?v={video_id}"
        published = e.get("published") or e.get("updated")
        thumb = None
        media_thumbnail = e.get("media_thumbnail") or []
        if media_thumbnail:
            thumb = media_thumbnail[0].get("url")

        topics = infer_topics(title)
        topic_stances = [{"topic": t, "stance": "neutral"} for t in topics]

        author = e.get("author") or e.get("yt_channelname") or None
        rows.append(
            {
                "video_id": video_id,
                "title": title,
                "source_url": link,
                "thumbnail_url": thumb,
                "published_at": published,
                "channel_name": author,
                "topics": topics,
                "topic_stances": topic_stances,
            }
        )
    return rows


def main() -> None:
    if not SEED_PATH.exists():
        raise SystemExit(f"seed file not found: {SEED_PATH}")

    seeds = json.loads(SEED_PATH.read_text(encoding="utf-8"))
    channels: list[dict] = []
    videos: list[dict] = []

    for s in seeds:
        handle = s.get("handle")
        cid = s.get("channel_id")
        avatar = s.get("channel_avatar_url")
        if not cid and handle:
            rcid, ravatar = resolve_channel_meta(handle)
            cid = rcid
            avatar = avatar or ravatar

        # Keep seed row even when cid resolve fails (so channel count stays stable)
        key_id = cid or str(handle or s.get("display_name") or "unknown-channel")

        channels.append(
            {
                "channel_id": key_id,
                "display_name": s.get("display_name") or handle or key_id,
                "handle": handle,
                "category_primary": s.get("category_primary", "macro"),
                "channel_avatar_url": avatar,
            }
        )

        if not cid:
            continue

        feed_rows = parse_feed(cid)
        for row in feed_rows:
            row["channel_id"] = cid
            row["channel_name"] = row.get("channel_name") or s.get("display_name") or handle or cid
            row["channel_avatar_url"] = avatar
            videos.append(row)

    videos.sort(key=lambda x: str(x.get("published_at") or ""), reverse=True)
    topics = sorted({t for v in videos for t in (v.get("topics") or [])})

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "channels": channels,
        "topics": topics,
        "videos": videos,
    }

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"written: {OUT_PATH} (channels={len(channels)}, videos={len(videos)})")


if __name__ == "__main__":
    main()
