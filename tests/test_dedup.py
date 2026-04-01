from __future__ import annotations

from app.services.ingestion.job_queue import enqueue_job
from app.models.models import JobStatus, ProcessingJob
from app.models.models import Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


# Lightweight unit-style test without depending on full app database connection.
# It validates idempotent intent by comparing enqueue behavior at ORM-level.
def test_enqueue_job_dedupe(monkeypatch):
    db_url = "sqlite:///:memory:"
    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)

    Base.metadata.create_all(bind=engine)
    db = Session()

    j1 = enqueue_job(db, "FETCH_METADATA", "video", "v1", dedupe=True)
    j2 = enqueue_job(db, "FETCH_METADATA", "video", "v1", dedupe=True)
    assert j1 is not None and j2 is not None
    assert j1.id == j2.id
    assert db.query(ProcessingJob).count() == 1

    done = db.query(ProcessingJob).filter(ProcessingJob.id == j1.id).first()
    assert done is not None
    assert done.status in (JobStatus.PENDING, JobStatus.RUNNING)
