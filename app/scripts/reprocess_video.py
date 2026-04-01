from __future__ import annotations

from app.db.base import SessionLocal
from app.models.models import JobType, Video
from app.services.ingestion.job_queue import enqueue_job


def main(video_id: str) -> None:
    db = SessionLocal()
    v = db.query(Video).filter(Video.video_id == video_id).first()
    if not v:
        raise SystemExit("video not found")
    enqueue_job(db, JobType.FETCH_METADATA.value, "video", str(v.id), dedupe=False)
    print({"ok": True, "job": "FETCH_METADATA", "video_id": video_id})


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        raise SystemExit("usage: python reprocess_video.py <video_id>")
    main(sys.argv[1])
