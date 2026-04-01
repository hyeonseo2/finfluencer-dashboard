from __future__ import annotations

import logging
import sqlite3
import tempfile
import threading
from dataclasses import dataclass
from datetime import timezone
from pathlib import Path
from typing import Optional

from app.core.config import settings

logger = logging.getLogger(__name__)


def _is_sqlite_db_url(database_url: str) -> bool:
    return database_url.startswith("sqlite:///")


def _resolve_sqlite_path(database_url: str) -> Path:
    if not _is_sqlite_db_url(database_url):
        raise ValueError("not a sqlite database_url")
    # sqlite:////abs/path.db -> abs/path.db
    # sqlite:///rel/path.db -> rel/path.db under CWD
    raw_path = database_url.removeprefix("sqlite:///")
    p = Path(raw_path)
    if not p.is_absolute():
        p = Path.cwd() / p
    return p.resolve()


def _get_bucket_and_blob_name() -> tuple[str, str]:
    bucket = settings.sqlite_backup_bucket
    if not bucket:
        raise RuntimeError("sqlite backup bucket is not configured")
    prefix = settings.sqlite_backup_prefix.strip("/")
    db_file = _resolve_sqlite_path(settings.database_url).name
    blob_name = f"{prefix}/{db_file}" if prefix else db_file
    return bucket, blob_name




def _has_seeded_data(path: Path) -> bool:
    """Return True if db has at least one channel/video row."""
    try:
        conn = sqlite3.connect(path)
        try:
            cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='channels'")
            if not cur.fetchone():
                return False
            channel_count = conn.execute("SELECT COUNT(*) FROM channels").fetchone()[0] or 0
            if channel_count > 0:
                return True
            video_count = conn.execute("SELECT COUNT(*) FROM videos").fetchone()[0] or 0
            return video_count > 0
        finally:
            conn.close()
    except Exception:
        return False

def _get_storage_client():
    try:
        from google.cloud import storage  # type: ignore
    except Exception as exc:
        raise RuntimeError("google-cloud-storage not installed") from exc
    return storage.Client()


def _snapshot_sqlite_db(path: Path) -> Path:
    """Create a consistent sqlite backup copy for upload."""
    dst = Path(tempfile.mkstemp(prefix="finfluencer-sqlite-backup-", suffix=".db")[1])
    src = path.resolve()
    source_conn = sqlite3.connect(f"file:{src}?mode=ro", uri=True)
    try:
        target_conn = sqlite3.connect(dst)
        try:
            source_conn.backup(target_conn)
        finally:
            target_conn.close()
    finally:
        source_conn.close()
    return dst



def restore_sqlite_db_if_needed() -> dict[str, object]:
    """Restore sqlite db from GCS if available and newer than local file."""
    out: dict[str, object] = {"restored": False, "reason": None, "remote_updated": None}

    if not settings.enable_sqlite_persistence:
        out["reason"] = "persistence-disabled"
        return out

    if not _is_sqlite_db_url(settings.database_url):
        out["reason"] = "non-sqlite-database"
        return out

    try:
        local_path = _resolve_sqlite_path(settings.database_url)
        bucket_name, blob_name = _get_bucket_and_blob_name()
        client = _get_storage_client()
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(blob_name)

        if not blob.exists():
            out["reason"] = "remote-missing"
            return out

        local_mtime: float = local_path.stat().st_mtime if local_path.exists() else 0.0
        local_has_data = _has_seeded_data(local_path)
        remote_updated = blob.updated
        if remote_updated is None:
            remote_updated_ts = 0.0
            out["remote_updated"] = None
        else:
            remote_updated_ts = remote_updated.replace(tzinfo=timezone.utc).timestamp()
            out["remote_updated"] = remote_updated.isoformat()

        if local_path.exists() and local_has_data and local_mtime >= remote_updated_ts:
            out["reason"] = "local-newer"
            return out

        local_path.parent.mkdir(parents=True, exist_ok=True)
        blob.download_to_filename(str(local_path))
        out["restored"] = True
        out["reason"] = "downloaded"
        return out
    except Exception as exc:
        logger.warning("sqlite restore failed: %s", exc)
        out["reason"] = f"restore-failed: {exc!r}"
        return out


@dataclass
class _PersistenceState:
    stop_event: threading.Event
    thread: Optional[threading.Thread]
    last_uploaded_mtime: float


class SqlitePersistenceWorker:
    def __init__(self) -> None:
        self._state: Optional[_PersistenceState] = None

    def _upload_once(self, local_path: Path, bucket_name: str, blob_name: str) -> bool:
        if not local_path.exists() or local_path.stat().st_size <= 0:
            logger.debug("sqlite upload skipped: empty db path=%s", local_path)
            return False

        snapshot = _snapshot_sqlite_db(local_path)
        try:
            client = _get_storage_client()
            bucket = client.bucket(bucket_name)
            blob = bucket.blob(blob_name)
            blob.upload_from_filename(str(snapshot))
            return True
        finally:
            try:
                snapshot.unlink()
            except OSError:
                pass

    def start(self) -> None:
        if not settings.enable_sqlite_persistence:
            logger.info("sqlite persistence disabled")
            return
        if not _is_sqlite_db_url(settings.database_url):
            logger.info("sqlite persistence skipped (non-sqlite DB)")
            return

        try:
            local_path = _resolve_sqlite_path(settings.database_url)
            bucket_name, blob_name = _get_bucket_and_blob_name()
        except Exception as exc:
            logger.warning("sqlite persistence not started: %s", exc)
            return

        interval = max(60, settings.sqlite_persistence_interval_seconds)
        stop_event = threading.Event()
        state = _PersistenceState(stop_event=stop_event, thread=None, last_uploaded_mtime=0.0)

        def _run() -> None:
            while not state.stop_event.wait(interval):
                try:
                    local_mtime = local_path.stat().st_mtime if local_path.exists() else 0.0
                    if local_mtime > state.last_uploaded_mtime + 1:
                        uploaded = self._upload_once(local_path, bucket_name, blob_name)
                        if uploaded:
                            state.last_uploaded_mtime = local_path.stat().st_mtime
                            logger.info("sqlite backup uploaded: %s", blob_name)
                except Exception as exc:
                    logger.exception("sqlite backup worker error: %s", exc)

        thread = threading.Thread(target=_run, name="sqlite-persistence", daemon=True)
        state.thread = thread
        self._state = state
        thread.start()
        logger.info(
            "sqlite persistence worker started interval=%ss bucket=%s blob=%s",
            interval,
            bucket_name,
            blob_name,
        )

    def stop(self) -> None:
        state = self._state
        if not state:
            return
        state.stop_event.set()
        if state.thread and state.thread.is_alive():
            state.thread.join(timeout=5.0)

        if not settings.enable_sqlite_persistence or not _is_sqlite_db_url(settings.database_url):
            self._state = None
            return
        try:
            local_path = _resolve_sqlite_path(settings.database_url)
            bucket_name, blob_name = _get_bucket_and_blob_name()
            if local_path.exists():
                uploaded = self._upload_once(local_path, bucket_name, blob_name)
                if uploaded:
                    logger.info("sqlite final backup uploaded: %s", blob_name)
        except Exception as exc:
            logger.warning("sqlite final backup failed: %s", exc)

        self._state = None


_sqlite_worker = SqlitePersistenceWorker()


def start_sqlite_persistence() -> dict[str, object]:
    result = restore_sqlite_db_if_needed()
    _sqlite_worker.start()
    return result


def stop_sqlite_persistence() -> None:
    _sqlite_worker.stop()




def force_upload_sqlite_backup(force: bool = False) -> dict[str, object]:
    """Immediately upload current sqlite snapshot to GCS (best-effort)."""
    out: dict[str, object] = {"uploaded": False, "reason": None}

    if not settings.enable_sqlite_persistence:
        out["reason"] = "persistence-disabled"
        return out
    if not _is_sqlite_db_url(settings.database_url):
        out["reason"] = "non-sqlite-database"
        return out

    try:
        local_path = _resolve_sqlite_path(settings.database_url)
        bucket_name, blob_name = _get_bucket_and_blob_name()
    except Exception as exc:
        out["reason"] = f"{exc!r}"
        return out

    if not force and not _has_seeded_data(local_path):
        out["reason"] = "skipped-empty-db"
        return out

    # avoid creating a new worker; use a short helper worker instance only for upload
    # (the main background worker handles periodic cadence).
    try:
        worker = SqlitePersistenceWorker()
        uploaded = worker._upload_once(local_path, bucket_name, blob_name)
        out["uploaded"] = uploaded
        out["reason"] = "ok" if uploaded else "no-changes"
    except Exception as exc:
        out["reason"] = f"{exc!r}"
    return out


__all__ = [
    "restore_sqlite_db_if_needed",
    "start_sqlite_persistence",
    "stop_sqlite_persistence",
    "force_upload_sqlite_backup",
]
