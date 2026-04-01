from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.core.config import settings
from app.db.base import get_db
from app.models.models import Channel, ChannelSyncState, JobType, ProcessingJob, Video, Analysis
from app.services.ingestion.job_queue import enqueue_job, get_active_channels_for_poll, pop_next_jobs, set_job_done, set_job_failed
from app.services.ingestion.channel_ingest import process_channel_feed
from app.services.youtube.client import resolve_channel_by_handle
from app.services.ingestion.rss_poller import parse_feed
from app.schemas.schemas import ChannelCreate, ResolveHandleIn, ResolveHandleOut
from app.services.ingestion.pipeline import ingest_metadata_batch, run_analyze_job, run_transcript_job
from app.db.sqlite_persistence import force_upload_sqlite_backup

router = APIRouter(prefix="/admin", dependencies=[Depends(require_admin)], tags=["admin"])


def _dispatch_job(db: Session, job) -> str:
    if job.job_type == JobType.FETCH_METADATA.value:
        return ingest_metadata_batch(db, job)
    if job.job_type == JobType.TRANSCRIPT.value:
        return run_transcript_job(db, job)
    if job.job_type == JobType.ANALYZE.value:
        return run_analyze_job(db, job)
    raise HTTPException(status_code=400, detail=f"Unsupported job_type={job.job_type}")



def _seed_channels(db: Session, rows: list[dict]) -> dict[str, int]:
    created = 0
    existed = 0
    skipped = 0
    for r in rows:
        handle = r.get("handle")
        channel_id = r.get("channel_id")
        display_name = r.get("display_name")

        if not channel_id and handle:
            resolved = resolve_channel_by_handle(handle)
            channel_id = resolved["channel_id"]
            display_name = resolved["display_name"]

        if not channel_id or not display_name:
            skipped += 1
            continue

        if db.query(Channel).filter(Channel.channel_id == channel_id).first():
            existed += 1
            continue

        ch = Channel(
            channel_id=channel_id,
            handle=handle,
            display_name=display_name,
            category_primary=r.get("category_primary", "macro"),
            country=r.get("country", "KR"),
            language=r.get("language", "ko"),
            is_interview_heavy=r.get("is_interview_heavy", False),
            active=r.get("active", True),
        )
        db.add(ch)
        db.flush()
        db.add(ChannelSyncState(channel_id=ch.id))
        created += 1

    return {"created": created, "existed": existed, "skipped": skipped}


@router.post("/channels")
def create_channel(payload: ChannelCreate, db: Session = Depends(get_db)) -> dict:
    if not payload.channel_id and not payload.handle:
        raise HTTPException(status_code=400, detail="channel_id or handle required")

    channel_id = payload.channel_id
    display_name = payload.display_name
    if not channel_id and payload.handle:
        resolved = resolve_channel_by_handle(payload.handle)
        channel_id = resolved["channel_id"]
        display_name = resolved["display_name"]

    if db.query(Channel).filter(Channel.channel_id == channel_id).first():
        raise HTTPException(status_code=409, detail="channel already exists")

    ch = Channel(
        channel_id=channel_id,
        handle=payload.handle,
        display_name=display_name,
        category_primary=payload.category_primary,
        country=payload.country,
        language=payload.language,
        is_interview_heavy=payload.is_interview_heavy,
        active=payload.active,
    )
    db.add(ch)
    db.flush()
    db.add(ChannelSyncState(channel_id=ch.id))
    db.commit()
    return {"ok": True, "channel_id": ch.channel_id}


@router.post("/videos/{video_id}/reanalyze")
def reanalyze_video(video_id: str, db: Session = Depends(get_db)) -> dict:
    v = db.query(Video).filter(Video.video_id == video_id).first()
    if not v:
        raise HTTPException(status_code=404, detail="video not found")

    db.query(Analysis).filter(Analysis.video_id == v.id).delete(synchronize_session=False)
    db.commit()
    enqueue_job(db, JobType.ANALYZE.value, "video", str(v.id), dedupe=False)
    return {"ok": True, "job": "ANALYZE", "video_id": video_id}




@router.post("/videos/backfill_published_from_feed")
def backfill_published_from_feed(db: Session = Depends(get_db)) -> dict:
    channels = get_active_channels_for_poll(db)
    updated = 0
    for ch in channels:
        entries, _, _ = parse_feed(ch.channel_id, None, None)
        id_to_date = {e["video_id"]: e.get("published_at") for e in entries if e.get("video_id")}
        if not id_to_date:
            continue
        for vid, dtv in id_to_date.items():
            if dtv is None:
                continue
            v = db.query(Video).filter(Video.video_id == vid, Video.published_at.is_(None)).first()
            if not v:
                continue
            v.published_at = dtv
            updated += 1
    db.commit()
    return {"updated": updated}


@router.post("/videos/backfill_published")
def backfill_video_published_at(db: Session = Depends(get_db)) -> dict:
    rows = db.query(Video).filter(Video.published_at.is_(None)).limit(1000).all()
    count = 0
    for v in rows:
        enqueue_job(db, "FETCH_METADATA", "video", str(v.id), dedupe=False)
        count += 1
    db.commit()
    return {"queued": count}


@router.post("/videos/reanalyze_all")
def reanalyze_all(limit: int = 200, db: Session = Depends(get_db)) -> dict:
    rows = db.query(Video).order_by(Video.id.desc()).limit(limit).all()
    count = 0
    for v in rows:
        db.query(Analysis).filter(Analysis.video_id == v.id).delete(synchronize_session=False)
        enqueue_job(db, JobType.ANALYZE.value, "video", str(v.id), dedupe=False)
        count += 1
    db.commit()
    return {"ok": True, "jobs_queued": count}


@router.post("/channels/resolve", response_model=ResolveHandleOut)
def resolve_channel(payload: ResolveHandleIn):
    data = resolve_channel_by_handle(payload.handle)
    return ResolveHandleOut(handle=payload.handle, channel_id=data["channel_id"], display_name=data["display_name"])


@router.post("/videos/{video_id}/reprocess")
def reprocess_video(video_id: str, db: Session = Depends(get_db)) -> dict:
    v = db.query(Video).filter(Video.video_id == video_id).first()
    if not v:
        raise HTTPException(status_code=404, detail="video not found")
    enqueue_job(db, JobType.FETCH_METADATA.value, "video", str(v.id), dedupe=False)
    return {"ok": True, "job": "FETCH_METADATA", "video_id": video_id}


@router.post("/videos/reprocess_all")
def reprocess_all(
    channel_id: str | None = None,
    limit: int = 0,
    dedupe: bool = False,
    db: Session = Depends(get_db),
) -> dict:
    query = db.query(Video)
    if channel_id:
        query = query.join(Channel).filter(Channel.channel_id == channel_id)
    if limit > 0:
        query = query.limit(limit)

    rows = query.all()
    for v in rows:
        enqueue_job(db, JobType.FETCH_METADATA.value, "video", str(v.id), dedupe=dedupe)
    db.commit()
    return {"ok": True, "jobs_queued": len(rows), "target": channel_id or "ALL", "dedupe": dedupe}


@router.post("/videos/{video_id}/retranscribe")
def retranscribe(video_id: str, db: Session = Depends(get_db)) -> dict:
    v = db.query(Video).filter(Video.video_id == video_id).first()
    if not v:
        raise HTTPException(status_code=404, detail="video not found")
    enqueue_job(db, JobType.TRANSCRIPT.value, "video", str(v.id), dedupe=False)
    return {"ok": True, "job": "TRANSCRIPT", "video_id": video_id}


@router.post("/backfill/channel/{channel_id}")
def backfill(channel_id: str, db: Session = Depends(get_db)) -> dict:
    ch = db.query(Channel).filter(Channel.channel_id == channel_id).first()
    if not ch:
        try:
            ch = db.query(Channel).filter(Channel.id == int(channel_id)).first()
        except Exception:
            ch = None
    if not ch:
        raise HTTPException(status_code=404, detail="channel not found")

    out = process_channel_feed(db, ch)
    return out


@router.post("/run_once")
def run_once(limit: int = 0, drain: bool = True, db: Session = Depends(get_db)) -> dict:
    # one-shot collector + job processor
    channels = get_active_channels_for_poll(db)
    collected = 0
    for ch in channels:
        out = process_channel_feed(db, ch)
        collected += out["new_count"]

    done = 0
    failed = 0
    loops = 0
    max_loops = 50
    total_cap = limit if limit and limit > 0 else None

    while (total_cap is None or done < total_cap) and (not drain and done == 0 or drain):
        remaining = (total_cap - done) if total_cap is not None else None
        batch_limit = min(remaining, settings.worker_batch_size) if remaining else settings.worker_batch_size
        if batch_limit <= 0:
            break

        jobs = pop_next_jobs(db, limit=batch_limit)
        if not jobs:
            break

        loops += 1
        for job in jobs:
            try:
                _dispatch_job(db, job)
                set_job_done(db, job)
                done += 1
            except Exception:
                set_job_failed(db, job, "run_once execution failed")
                failed += 1

        # avoid very long synchronous runs in shared/managed environments
        if not drain or loops >= max_loops:
            break

    persistence = force_upload_sqlite_backup()
    return {
        "channels_processed": len(channels),
        "new_videos": collected,
        "jobs_processed": done,
        "jobs_failed": failed,
        "jobs_drained": done,
        "loops": loops,
        "drain": drain,
        "limit": limit,
        "persistence": persistence,
    }


@router.get("/jobs")
def list_jobs(limit: int = 100, db: Session = Depends(get_db)) -> list[dict]:
    rows = db.query(ProcessingJob).order_by(ProcessingJob.id.desc()).limit(limit).all()
    return [
        {
            "id": r.id,
            "job_type": r.job_type,
            "entity_type": r.entity_type,
            "entity_id": r.entity_id,
            "status": r.status,
            "attempts": r.attempts,
            "last_error": r.last_error,
            "scheduled_at": r.scheduled_at,
            "started_at": r.started_at,
            "finished_at": r.finished_at,
        }
        for r in rows
    ]


@router.get("/jobs/{job_id}")
def get_job(job_id: int, db: Session = Depends(get_db)):
    r = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="job not found")
    return {
        "id": r.id,
        "job_type": r.job_type,
        "entity_type": r.entity_type,
        "entity_id": r.entity_id,
        "status": r.status,
        "attempts": r.attempts,
        "last_error": r.last_error,
        "scheduled_at": r.scheduled_at,
        "started_at": r.started_at,
        "finished_at": r.finished_at,
    }


@router.post("/bootstrap")
def bootstrap(seed_path: str = "sample_seed_channels.json", do_run_once: bool = False, db: Session = Depends(get_db)) -> dict:
    seed_file = Path(__file__).resolve().parents[2] / seed_path
    if not seed_file.exists():
        # fallback: treat as absolute/relative workspace path
        seed_file = Path(seed_path)
    if not seed_file.exists():
        raise HTTPException(status_code=400, detail=f"seed file not found: {seed_path}")

    with seed_file.open("r", encoding="utf-8") as f:
        rows = json.load(f)

    summary = _seed_channels(db, rows)
    db.commit()

    out = {
        "ok": True,
        "seed_path": str(seed_file),
        "created": summary["created"],
        "existed": summary["existed"],
        "skipped": summary["skipped"],
    }

    if do_run_once:
        run_once_result = run_once(db=db)
        persistence_result = force_upload_sqlite_backup()
        run_once_result["persistence"] = persistence_result
        out.update(run_once=run_once_result)

    return out
