from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.models import IngestStatus, Transcript, TranscriptStatus, Video
from app.services.analysis.analyzer import get_analysis_provider
from app.services.ingestion.job_queue import enqueue_job
from app.services.transcript.interfaces import TranscriptResult
from app.services.transcript.public_transcript import PublicTranscriptProvider
from app.services.transcript.stt_fallback import FallbackTranscriptProvider
from app.services.youtube.client import fetch_videos_metadata


PUBLIC_PROVIDER = PublicTranscriptProvider()
STT_PROVIDER = FallbackTranscriptProvider()


def upsert_video_from_feed(db: Session, channel_db_obj, parsed_item: dict) -> Video:
    v = db.query(Video).filter(Video.video_id == parsed_item["video_id"]).first()
    if v:
        return v

    v = Video(
        video_id=parsed_item["video_id"],
        channel_id=channel_db_obj.id,
        title=parsed_item.get("title"),
        description=None,
        published_at=parsed_item.get("published_at"),
        is_short=False,
        is_live=False,
        is_upcoming=False,
        caption_available=False,
        source_url=parsed_item.get("source_url"),
        ingest_status=IngestStatus.NEW,
        transcript_status=TranscriptStatus.SKIPPED,
    )
    db.add(v)
    db.flush()
    enqueue_job(db, "FETCH_METADATA", "video", str(v.id), dedupe=True)
    db.commit()
    db.refresh(v)
    return v


def ingest_metadata_batch(db: Session, job: Any) -> str:
    video = db.query(Video).filter(Video.id == int(job.entity_id)).first()
    if not video:
        raise RuntimeError("video missing")

    items = fetch_videos_metadata([video.video_id])
    if not items:
        video.ingest_status = IngestStatus.FAILED
        db.add(video)
        db.commit()
        raise RuntimeError("videos.list returned no item")

    item = items[0]
    video.title = item["title"]
    video.description = item["description"]
    if item.get("published_at") is not None:
        video.published_at = item.get("published_at")
    video.duration_sec = item["duration_sec"]
    video.is_live = bool(item["is_live"])
    video.is_upcoming = bool(item["is_upcoming"])
    video.caption_available = bool(item["caption_available"])
    video.view_count = item["view_count"]
    video.like_count = item["like_count"]
    video.comment_count = item["comment_count"]
    video.thumbnail_url = item["thumbnail_url"]
    video.ingest_status = IngestStatus.METADATA_DONE
    db.add(video)
    db.commit()
    enqueue_job(db, "TRANSCRIPT", "video", str(video.id), dedupe=True)
    return video.video_id


def _save_transcript(db: Session, video: Video, result: TranscriptResult) -> None:
    t = Transcript(
        video_id=video.id,
        source_type=result.provider_name,
        language_code=result.language_code,
        text_full=result.text,
        segments_json=[s.__dict__ for s in result.segments],
        provider_name=result.provider_name,
        provider_version=result.provider_version,
        status=TranscriptStatus.SUCCESS,
    )
    db.add(t)


def run_transcript_job(db: Session, job) -> str:
    video = db.query(Video).filter(Video.id == int(job.entity_id)).first()
    if not video:
        raise RuntimeError("video missing")

    last = (
        db.query(Transcript)
        .filter(Transcript.video_id == video.id)
        .filter(Transcript.status == TranscriptStatus.SUCCESS)
        .order_by(Transcript.created_at.desc())
        .first()
    )
    if last:
        video.transcript_status = TranscriptStatus.SUCCESS
        db.add(video)
        db.commit()
        enqueue_job(db, "ANALYZE", "video", str(video.id), dedupe=True)
        return f"already-have-transcript:{video.video_id}"

    providers = [PUBLIC_PROVIDER, STT_PROVIDER]
    if settings.transcript_provider_preferred == "stt_fallback":
        providers = [STT_PROVIDER, PUBLIC_PROVIDER]

    result = None
    stt_error_msg = None
    for provider in providers:
        if result:
            break
        try:
            result = provider.get_transcript(video.video_id)
            stt_error_msg = None
        except Exception as e:  # noqa: PERF203
            if provider is STT_PROVIDER:
                stt_error_msg = str(e)

    if result:
        _save_transcript(db, video, result)
        video.transcript_status = TranscriptStatus.SUCCESS
    else:
        # If no provider produced transcript, keep SKIPPED when STT is intentionally not available.
        # Otherwise, mark FAILED so worker retry semantics remain clear.
        if stt_error_msg and "STT not implemented in MVP runtime" in stt_error_msg:
            video.transcript_status = TranscriptStatus.SKIPPED
        else:
            video.transcript_status = TranscriptStatus.FAILED

    video.ingest_status = IngestStatus.TRANSCRIPT_DONE
    db.add(video)
    db.commit()

    # continue pipeline even when transcript unavailable
    enqueue_job(db, "ANALYZE", "video", str(video.id), dedupe=True)
    return video.video_id



def run_analyze_job(db: Session, job) -> str:
    from app.models.models import Analysis

    video = db.query(Video).filter(Video.id == int(job.entity_id)).first()
    if not video:
        raise RuntimeError("video missing")

    existing = db.query(Analysis).filter(Analysis.video_id == video.id).first()
    if existing:
        video.ingest_status = IngestStatus.ANALYZED
        db.add(video)
        db.commit()
        return "already"

    transcript_obj = (
        db.query(Transcript)
        .filter(Transcript.video_id == video.id, Transcript.status == TranscriptStatus.SUCCESS)
        .order_by(Transcript.created_at.desc())
        .first()
    )
    transcript_text = transcript_obj.text_full if transcript_obj else None

    provider = get_analysis_provider()
    parsed = provider.analyze(video.title or "", video.description, transcript_text)
    payload = parsed.payload
    obj = Analysis(
        video_id=video.id,
        model_provider=parsed.model_provider,
        model_name=parsed.model_name,
        prompt_version=parsed.prompt_version,
        taxonomy_version=parsed.taxonomy_version,
        summary=payload.summary,
        topics_json=payload.topics,
        topic_stances_json=[x.dict() for x in payload.topic_stances],
        signals_json=[x.dict() for x in payload.signals],
        mentioned_assets_json=payload.mentioned_assets,
        risk_flags_json=payload.risk_flags,
        confidence_overall=(
            sum((x.confidence or 0) for x in payload.topic_stances) / max(1, len(payload.topic_stances))
            if payload.topic_stances
            else None
        ),
        subject_type="channel",
        raw_output_json=payload.model_dump(),
    )
    db.add(obj)
    video.ingest_status = IngestStatus.ANALYZED
    db.add(video)
    db.commit()
    return video.video_id
