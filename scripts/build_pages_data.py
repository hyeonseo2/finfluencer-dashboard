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




def resolve_channel_id_from_handle(handle: str) -> str | None:
    if not handle:
        return None
    h = handle if handle.startswith('@') else f'@{handle}'
    url = f'https://www.youtube.com/{h}'
    try:
        r = requests.get(url, timeout=15, headers={'User-Agent':'Mozilla/5.0'})
        if not r.ok:
            return None
        m = re.search(r'"channelId"\s*:\s*"(UC[\w-]{20,})"', r.text)
        if m:
            return m.group(1)
    except Exception:
        return None
    return None

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
        cid = s.get("channel_id")
        if not cid and s.get("handle"):
            cid = resolve_channel_id_from_handle(s.get("handle"))
        if not cid:
            continue

        channels.append(
            {
                "channel_id": cid,
                "display_name": s.get("display_name") or s.get("handle") or cid,
                "handle": s.get("handle"),
                "category_primary": s.get("category_primary", "macro"),
            }
        )

        feed_rows = parse_feed(cid)
        for row in feed_rows:
            row["channel_id"] = cid
            row["channel_name"] = row.get("channel_name") or s.get("display_name") or s.get("handle") or cid
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
    print(f"written: {OUT_PATH} (videos={len(videos)})")


if __name__ == "__main__":
    main()
