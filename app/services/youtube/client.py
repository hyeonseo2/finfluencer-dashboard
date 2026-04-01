from __future__ import annotations

import datetime as dt
import html as _html
import json
import re
from typing import Any

import requests

from app.core.config import settings


class YouTubeApiError(RuntimeError):
    pass


def _get(url: str, params: dict[str, str]) -> dict[str, Any]:
    r = requests.get(url, params=params, timeout=30)
    if r.status_code >= 400:
        raise YouTubeApiError(f"YouTube API error {r.status_code}: {r.text[:500]}")
    return r.json()


def _parse_iso8601_duration_to_seconds(iso: str | None) -> int | None:
    if not iso:
        return None
    # PTxHMyMS fallback parser
    pattern = r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?"
    m = re.match(pattern, iso)
    if not m:
        return None
    h = int(m.group(1) or 0)
    mi = int(m.group(2) or 0)
    s = int(m.group(3) or 0)
    return h * 3600 + mi * 60 + s


def parse_iso_dt(dt_str: str | None):
    if not dt_str:
        return None
    try:
        return dt.datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    except Exception:
        return None


def _safe_int(raw: Any) -> int | None:
    try:
        if raw is None:
            return None
        return int(raw)
    except Exception:
        return None


def resolve_channel_by_handle(handle: str) -> dict:
    """Resolve handle to channel_id.

    1) Prefer official API when key exists.
    2) Fallback scraping on public page HTML and extract UC... id.
    """
    handle = handle.lstrip("@").strip()

    if settings.youtube_api_key:
        data = _get(
            f"{settings.yt_api_base}/channels",
            {
                "part": "snippet",
                "forHandle": handle,
                "key": settings.youtube_api_key,
            },
        )
        items = data.get("items") or []
        if not items:
            raise YouTubeApiError("No channel found for handle")
        item = items[0]
        return {
            "channel_id": item["id"],
            "display_name": item["snippet"]["title"],
        }

    candidates = [
        f"https://www.youtube.com/@{handle}/videos",
        f"https://www.youtube.com/@{handle}",
        f"https://www.youtube.com/c/{handle}",
    ]

    for page in candidates:
        try:
            resp = requests.get(page, headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
            text_html = resp.text
            for pat in [
                r'"externalId"\s*:\s*"(UC[0-9A-Za-z_-]{20,24})"',
                r'"browseId"\s*:\s*"(UC[0-9A-Za-z_-]{20,24})"',
                r'"channelId"\s*:\s*"(UC[0-9A-Za-z_-]{20,24})"',
            ]:
                m = re.search(pat, text_html)
                if m:
                    cid = m.group(1)
                    title_match = re.search(r"<title>([^<]+)</title>", text_html)
                    title = (title_match.group(1) if title_match else handle).replace(' - YouTube', '').strip()
                    return {"channel_id": cid, "display_name": title}
        except Exception:
            continue

    raise YouTubeApiError("No channel found for handle")


def _parse_iso_datetime(raw: str | None):
    if not raw:
        return None
    try:
        return dt.datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except Exception:
        return None


def _parse_player_response(html: str) -> dict[str, Any] | None:
    marker = "ytInitialPlayerResponse"
    idx = html.find(marker)
    if idx < 0:
        return None

    eq = html.find("=", idx)
    if eq < 0:
        return None
    cur = eq + 1
    while cur < len(html) and html[cur].isspace():
        cur += 1
    if cur >= len(html) or html[cur] != "{":
        return None

    # naive brace matcher for the JSON object
    depth = 0
    end = None
    for i in range(cur, len(html)):
        ch = html[i]
        if ch == "{":
            depth += 1
        elif ch == "}" and depth:
            depth -= 1
            if depth == 0:
                end = i
                break
    if not end:
        return None

    raw = html[cur : end + 1]
    try:
        return json.loads(raw)
    except Exception:
        return None


def _extract_watch_metadata(video_id: str) -> dict[str, object]:
    """Scrape public watch page for description/date fallback."""
    url = f"https://www.youtube.com/watch?v={video_id}"
    out: dict[str, object] = {}
    try:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
        if r.status_code != 200:
            return out
        html = r.text

        # date
        for pat in [
            r'"publishDate"\s*:\s*"(20\d{2}-\d{2}-\d{2}T[^\"]+)"',
            r'"uploadDate"\s*:\s*"(20\d{2}-\d{2}-\d{2}T[^\"]+)"',
            r'"datePublished"\s*:\s*"(20\d{2}-\d{2}-\d{2}T[^\"]+)"',
        ]:
            m = re.search(pat, html)
            if m:
                dtv = _parse_iso_datetime(m.group(1))
                if dtv:
                    out["published_at"] = dtv
                    break

        if "published_at" not in out:
            m = re.search(r'<meta itemprop="datePublished" content="([^"]+)"', html)
            if m:
                dtv = _parse_iso_datetime(m.group(1))
                if dtv:
                    out["published_at"] = dtv

        # description: multiple fallback strategies
        # 1) html meta tags are often stable across layout variants
        for pat in [
            r'property="og:description"\s+content="([^"]+)"',
            r'name="twitter:description"\s+content="([^"]+)"',
        ]:
            m = re.search(pat, html)
            if m:
                text = _html.unescape(m.group(1)).replace("\\n", "\n").strip()
                if text:
                    out["description"] = text
                    break

        # 2) player JSON shortDescription (if available)
        if "description" not in out:
            player = _parse_player_response(html)
            if player:
                try:
                    desc = None
                    vdetail = (((player.get("videoDetails") or {}).get("shortDescription") or "") if isinstance(player, dict) else "")
                    if vdetail:
                        desc = vdetail
                    if not desc:
                        # microformat description often contains escaped HTML text
                        mf = (player.get("microformat") or {}).get("playerMicroformatRenderer") or {}
                        desc_candidates = [
                            mf.get("description"),
                            (mf.get("description") or {}).get("simpleText") if isinstance(mf.get("description"), dict) else None,
                        ]
                        for d in desc_candidates:
                            if d:
                                desc = d
                                break
                    if desc:
                        out["description"] = _html.unescape(desc).replace("\\n", "\n")
                except Exception:
                    pass

        # 3) pure regex fallback in raw HTML
        if "description" not in out:
            for pat in [
                r'"shortDescription"\s*:\s*"(.*?)"',
                r'"description"\s*:\s*\{\s*"simpleText"\s*:\s*"(.*?)"\s*\}',
            ]:
                m = re.search(pat, html, re.S)
                if m:
                    raw = m.group(1)
                    text = _html.unescape(raw).replace("\\n", "\n")
                    if text:
                        out["description"] = text
                        break

    except Exception:
        pass
    return out


def _fetch_oembed_metadata(video_id: str) -> dict[str, object] | None:
    """Resolve lightweight public video metadata without API key."""
    url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
    try:
        r = requests.get(url, timeout=20)
        if r.status_code != 200:
            return None
        data = r.json()
        return {
            "title": data.get("title"),
            "author_name": data.get("author_name"),
            "thumbnail_url": data.get("thumbnail_url"),
            "video_id": video_id,
            "source_url": f"https://www.youtube.com/watch?v={video_id}",
        }
    except Exception:
        return None


def _fetch_watch_fallback(video_id: str) -> dict[str, object]:
    data = _extract_watch_metadata(video_id)
    return {
        "description": data.get("description"),
        "published_at": data.get("published_at"),
    }


def fetch_videos_metadata(video_ids: list[str]) -> list[dict]:
    if not video_ids:
        return []

    if not settings.youtube_api_key:
        # fallback mode: try public oEmbed metadata first, then scrape watch page.
        out: list[dict[str, object]] = []
        for vid in video_ids:
            meta = _fetch_oembed_metadata(vid)
            wmeta = _fetch_watch_fallback(vid)
            out.append(
                {
                    "video_id": vid,
                    "channel_id": None,
                    "title": meta.get("title") if isinstance(meta, dict) else None,
                    "description": (meta.get("description") if isinstance(meta, dict) and meta.get("description") else wmeta.get("description") if isinstance(wmeta, dict) else None),
                    "published_at": wmeta.get("published_at") if isinstance(wmeta, dict) else None,
                    "thumbnail_url": meta.get("thumbnail_url") if isinstance(meta, dict) else None,
                    "source_url": meta.get("source_url") if isinstance(meta, dict) else None,
                    "tags": [],
                    "duration_sec": None,
                    "caption_available": False,
                    "is_short": False,
                    "is_live": False,
                    "is_upcoming": False,
                    "view_count": None,
                    "like_count": None,
                    "comment_count": None,
                }
            )
        return out

    fields = "items(id,snippet/title,snippet/description,snippet/publishedAt,snippet/thumbnails/default/url,snippet/tags,snippet/channelId,snippet/liveBroadcastContent,contentDetails/duration,contentDetails/caption,statistics/viewCount,statistics/likeCount,statistics/commentCount)"
    data = _get(
        f"{settings.yt_api_base}/videos",
        {
            "part": "snippet,contentDetails,statistics",
            "id": ",".join(video_ids),
            "key": settings.youtube_api_key,
            "fields": fields,
        },
    )
    result = []
    for item in data.get("items", []):
        sn = item.get("snippet", {})
        cd = item.get("contentDetails", {})
        st = item.get("statistics", {})
        duration = cd.get("duration")
        duration_sec = _parse_iso8601_duration_to_seconds(duration)
        lbc = sn.get("liveBroadcastContent")
        result.append(
            {
                "video_id": item.get("id"),
                "channel_id": sn.get("channelId"),
                "title": sn.get("title"),
                "description": sn.get("description"),
                "published_at": parse_iso_dt(sn.get("publishedAt")),
                "thumbnail_url": ((sn.get("thumbnails") or {}).get("default") or {}).get("url"),
                "tags": sn.get("tags") or [],
                "duration_sec": duration_sec,
                "caption_available": str(cd.get("caption") or "").lower() == "true",
                "is_short": bool(duration_sec is not None and duration_sec <= 60),
                "is_live": lbc == "live",
                "is_upcoming": lbc == "upcoming",
                "view_count": _safe_int(st.get("viewCount")),
                "like_count": _safe_int(st.get("likeCount")),
                "comment_count": _safe_int(st.get("commentCount")),
            }
        )
    return result
