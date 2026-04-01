from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.models import JobStatus, ProcessingJob


def enqueue_job(
    db: Session,
    job_type: str,
    entity_type: str,
    entity_id: str,
    dedupe: bool = True,
    delay_seconds: int = 0,
) -> ProcessingJob | None:
    """Create a new job row.

    If dedupe=True, an already pending/running job for same tuple is returned instead of creating duplicate.
    """
    if dedupe:
        existing = (
            db.query(ProcessingJob)
            .filter(
                ProcessingJob.job_type == job_type,
                ProcessingJob.entity_type == entity_type,
                ProcessingJob.entity_id == entity_id,
                ProcessingJob.status.in_([JobStatus.PENDING, JobStatus.RUNNING]),
            )
            .first()
        )
        if existing:
            return existing

    job = ProcessingJob(
        job_type=job_type,
        entity_type=entity_type,
        entity_id=entity_id,
        status=JobStatus.PENDING,
        attempts=0,
        scheduled_at=datetime.now(timezone.utc) + timedelta(seconds=delay_seconds),
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def pop_next_jobs(db: Session, limit: int = 1) -> list[ProcessingJob]:
    now = datetime.now(timezone.utc)
    rows = (
        db.query(ProcessingJob)
        .filter(ProcessingJob.status == JobStatus.PENDING, ProcessingJob.scheduled_at <= now)
        .order_by(ProcessingJob.scheduled_at.asc(), ProcessingJob.id.asc())
        .limit(limit)
        .all()
    )

    for job in rows:
        job.status = JobStatus.RUNNING
        job.started_at = now
    db.commit()
    return rows


def set_job_done(db: Session, job: ProcessingJob) -> None:
    job.status = JobStatus.DONE
    job.finished_at = datetime.now(timezone.utc)
    job.last_error = None
    db.add(job)
    db.commit()


def set_job_failed(db: Session, job: ProcessingJob, err: str) -> None:
    attempts = job.attempts + 1
    job.attempts = attempts
    job.last_error = err[:1000]

    if attempts >= settings.retry_max_attempts:
        job.status = JobStatus.DLQ
        job.finished_at = datetime.now(timezone.utc)
    else:
        delay = int((settings.retry_backoff_base_seconds * (2 ** (attempts - 1))) ** 1.8)
        job.scheduled_at = datetime.now(timezone.utc) + timedelta(seconds=delay)
        job.status = JobStatus.PENDING
        job.started_at = None
    db.add(job)
    db.commit()


def get_dlq_jobs(db: Session, limit: int = 100) -> list[ProcessingJob]:
    return (
        db.query(ProcessingJob)
        .filter(ProcessingJob.status == JobStatus.DLQ)
        .order_by(ProcessingJob.id.desc())
        .limit(limit)
        .all()
    )


def get_active_channels_for_poll(db: Session):
    from app.models.models import Channel

    return db.query(Channel).filter(Channel.active.is_(True)).all()
