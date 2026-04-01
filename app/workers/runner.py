from __future__ import annotations

import logging
import time

from app.core.config import settings
from app.core.logging import init_logging
from app.db.base import SessionLocal
from app.models.models import JobType
from app.services.ingestion.job_queue import pop_next_jobs, set_job_done, set_job_failed
from app.services.ingestion.pipeline import ingest_metadata_batch, run_analyze_job, run_transcript_job

log = logging.getLogger("finfluencer.worker")


def _dispatch(job, db):
    if job.job_type == JobType.FETCH_METADATA.value:
        return ingest_metadata_batch(db, job)
    if job.job_type == JobType.TRANSCRIPT.value:
        return run_transcript_job(db, job)
    if job.job_type == JobType.ANALYZE.value:
        return run_analyze_job(db, job)
    raise RuntimeError(f"Unsupported job_type={job.job_type}")


def worker_loop() -> None:
    init_logging()
    log.info("worker started")
    while True:
        db = SessionLocal()
        try:
            jobs = pop_next_jobs(db, limit=settings.worker_batch_size)
            if not jobs:
                time.sleep(settings.worker_poll_interval_seconds)
                db.close()
                continue

            for job in jobs:
                try:
                    out = _dispatch(job, db)
                    set_job_done(db, job)
                    log.info("job_done", extra={"job_id": job.id, "video_id": job.entity_id, "result": out})
                except Exception as e:
                    set_job_failed(db, job, str(e))
                    log.exception("job_failed", extra={"job_id": job.id, "video_id": job.entity_id})
            db.close()
        except Exception:
            log.exception("runner_loop_error")
            db.close()
            time.sleep(2)


def main() -> None:
    worker_loop()


if __name__ == "__main__":
    main()
