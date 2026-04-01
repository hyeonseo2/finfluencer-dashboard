from __future__ import annotations

from datetime import datetime
from typing import Any
import re

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc
import requests
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.models.models import Analysis, Channel, IngestStatus, Transcript, Video
from app.schemas.schemas import DISCLAIMER, ChannelOut, OpinionCompareItem, VideoOut
from app.services.youtube.client import fetch_videos_metadata

router = APIRouter()

ALLOWED_TOPICS = {"macro", "real_estate", "stocks", "etf", "crypto", "fx", "bonds", "commodities", "policy", "interest_rate"}


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "disclaimer": DISCLAIMER}


@router.get("/channels", response_model=list[ChannelOut])
def list_channels(db: Session = Depends(get_db)) -> list[ChannelOut]:
    rows = db.query(Channel).filter(Channel.active.is_(True)).order_by(Channel.created_at.desc()).all()
    return [_channel_to_out(r) for r in rows]


@router.get("/channels/{channel_id}", response_model=ChannelOut)
def get_channel(channel_id: str, db: Session = Depends(get_db)) -> Channel:
    row = db.query(Channel).filter(Channel.channel_id == channel_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="channel not found")
    return _channel_to_out(row)


_CHANNEL_AVATAR_CACHE: dict[str, str | None] = {}


def _extract_channel_avatar(channel_id: str) -> str | None:
    if not channel_id:
        return None
    if channel_id in _CHANNEL_AVATAR_CACHE:
        return _CHANNEL_AVATAR_CACHE[channel_id]

    try:
        html = requests.get(
            f"https://www.youtube.com/channel/{channel_id}",
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=20,
        ).text
        match = re.search(r'property="og:image"\s+content="([^"]+)"', html)
        avatar = match.group(1) if match else None
    except Exception:
        avatar = None

    _CHANNEL_AVATAR_CACHE[channel_id] = avatar
    return avatar


def _ensure_title_and_meta_if_missing(db: Session, v: Video) -> None:
    if v.title:
        return


def _channel_to_out(ch: Channel) -> dict:
    return {
        "channel_id": ch.channel_id,
        "channel_avatar_url": _extract_channel_avatar(ch.channel_id),
        "handle": ch.handle,
        "display_name": ch.display_name,
        "category_primary": ch.category_primary,
        "country": ch.country,
        "language": ch.language,
        "is_interview_heavy": ch.is_interview_heavy,
        "active": ch.active,
    }


    try:
        meta_list = fetch_videos_metadata([v.video_id])
    except Exception:
        return

    if not meta_list:
        return
    meta = meta_list[0]
    if not isinstance(meta, dict):
        return
    title = meta.get("title")
    if title:
        v.title = title
    # keep non-null fields when oEmbed provides them
    if not v.source_url and meta.get("source_url"):
        v.source_url = meta.get("source_url")
    if v.published_at is None and meta.get("published_at") is not None:
        v.published_at = meta.get("published_at")
    if v.thumbnail_url is None and meta.get("thumbnail_url"):
        v.thumbnail_url = meta.get("thumbnail_url")
    if meta.get("description") and not v.description:
        v.description = meta.get("description")
    if meta.get("duration_sec") is not None:
        v.duration_sec = meta.get("duration_sec")
    if meta.get("caption_available") is not None:
        v.caption_available = bool(meta.get("caption_available"))

    db.add(v)
    try:
        db.commit()
        db.refresh(v)
    except Exception:
        db.rollback()


def _row_to_video_out(db: Session, v: Video) -> VideoOut:
    _ensure_title_and_meta_if_missing(db, v)
    an = db.query(Analysis).filter(Analysis.video_id == v.id).order_by(desc(Analysis.created_at)).first()
    transcript_preview = None
    if not an:
        tr = (
            db.query(Transcript)
            .filter(Transcript.video_id == v.id, Transcript.status == "SUCCESS")
            .order_by(desc(Transcript.created_at))
            .first()
        )
        if tr and tr.text_full:
            lines = [l.strip() for l in str(tr.text_full).splitlines() if l.strip()]
            transcript_preview = "\n".join(lines[:4]) or None

    if an and (an.summary or "").strip() == "요약 정보가 아직 수집되지 않았습니다....":
        an_summary = None
    else:
        an_summary = an.summary if an else None

    return VideoOut(
        video_id=v.video_id,
        title=v.title,
        channel=v.channel.display_name if v.channel else "",
        channel_id=v.channel.channel_id if v.channel else "",
        channel_avatar_url=_extract_channel_avatar(v.channel.channel_id) if v.channel else None,
        published_at=v.published_at,
        source_url=v.source_url,
        summary=an_summary,
        transcript_preview=transcript_preview,
        thumbnail_url=v.thumbnail_url,
        topics=(an.topics_json or []) if an else [],
        topic_stances=(an.topic_stances_json or []) if an else [],
        signals=(an.signals_json or []) if an else [],
        transcript_status=v.transcript_status,
    )


@router.get("/videos")
def list_videos(
    q: str | None = None,
    topic: str | None = None,
    channel_id: str | None = None,
    limit: int = 30,
    db: Session = Depends(get_db),
) -> list[VideoOut]:
    rows = db.query(Video)
    if q:
        rows = rows.filter(Video.title.ilike(f"%{q}%"))
    if channel_id:
        rows = rows.join(Channel).filter(Channel.channel_id == channel_id)

    row_list = rows.order_by(desc(Video.published_at)).limit(limit).all()
    if topic:
        if topic not in ALLOWED_TOPICS:
            topic = None
        filtered = []
        for v in row_list:
            an = db.query(Analysis).filter(Analysis.video_id == v.id).first()
            if an and topic in (an.topics_json or []):
                filtered.append(v)
        row_list = filtered

    return [_row_to_video_out(db, v) for v in row_list[:limit]]


@router.get("/videos/{video_id}")
def get_video(video_id: str, db: Session = Depends(get_db)) -> VideoOut:
    v = db.query(Video).filter(Video.video_id == video_id).first()
    if not v:
        raise HTTPException(status_code=404, detail="video not found")
    return _row_to_video_out(db, v)




@router.get("/topics")
def list_topics(db: Session = Depends(get_db)) -> list[str]:
    rows = db.query(Analysis.topics_json).filter(Analysis.topics_json.isnot(None)).all()
    uniq: set[str] = set()
    for (topics_json,) in rows:
        for t in topics_json or []:
            if isinstance(t, str) and t in ALLOWED_TOPICS:
                uniq.add(t)
    return sorted(uniq)


@router.get("/opinions/latest")
def latest_opinions(topic: str | None = None, limit: int = 30, db: Session = Depends(get_db)) -> list[VideoOut]:
    rows = (
        db.query(Video)
        .join(Analysis, Analysis.video_id == Video.id)
        .filter(Video.ingest_status == IngestStatus.ANALYZED)
        .order_by(Video.published_at.desc())
        .limit(limit)
        .all()
    )
    if topic:
        filtered = []
        for v in rows:
            an = db.query(Analysis).filter(Analysis.video_id == v.id).first()
            if an and topic in (an.topics_json or []):
                filtered.append(v)
        rows = filtered

    return [_row_to_video_out(db, v) for v in rows[:limit]]


@router.get("/opinions/compare")
def compare(topic: str, limit: int = 50, db: Session = Depends(get_db)) -> list[OpinionCompareItem]:
    rows = (
        db.query(Video, Analysis)
        .join(Analysis, Analysis.video_id == Video.id)
        .filter(Video.ingest_status == IngestStatus.ANALYZED)
        .order_by(Video.published_at.desc())
        .all()
    )

    out: list[OpinionCompareItem] = []
    for v, an in rows:
        stances = an.topic_stances_json or []
        for s in stances:
            if s.get("topic") != topic:
                continue
            excerpt = None
            evidence = s.get("evidence")
            if isinstance(evidence, list) and evidence and isinstance(evidence[0], dict):
                excerpt = evidence[0].get("quote_excerpt")

            out.append(
                OpinionCompareItem(
                    video_id=v.video_id,
                    channel=v.channel.display_name if v.channel else "",
                    title=v.title or "",
                    published_at=v.published_at,
                    topic=topic,
                    stance=s.get("stance"),
                    confidence=float(s.get("confidence")) if s.get("confidence") is not None else None,
                    evidence_excerpt=excerpt,
                    source_url=v.source_url,
                )
            )
            if len(out) >= limit:
                return out
    return out


@router.get("/opinions/trending")
def trending(topic: str, limit: int = 50, db: Session = Depends(get_db)) -> list[OpinionCompareItem]:
    return compare(topic=topic, limit=limit, db=db)


@router.get("/search")
def search(q: str, db: Session = Depends(get_db)) -> list[VideoOut]:
    return list_videos(q=q, db=db)
