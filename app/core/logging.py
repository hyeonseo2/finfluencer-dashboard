from __future__ import annotations

import json
import logging
import uuid
from contextvars import ContextVar

request_id_var = ContextVar("request_id", default=None)
job_id_var = ContextVar("job_id", default=None)
video_id_var = ContextVar("video_id", default=None)


def init_logging() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    class _JSONFormatter(logging.Formatter):
        def format(self, record: logging.LogRecord) -> str:  # type: ignore[override]
            payload = {
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
                "request_id": request_id_var.get(),
                "job_id": job_id_var.get(),
                "video_id": video_id_var.get(),
            }
            return json.dumps(payload, ensure_ascii=False, default=str)

    root = logging.getLogger()
    for h in root.handlers:
        h.setFormatter(_JSONFormatter())


def new_id() -> str:
    return str(uuid.uuid4())
