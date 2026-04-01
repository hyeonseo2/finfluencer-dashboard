from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


class IngestStatus(str, Enum):
    NEW = "NEW"
    METADATA_DONE = "METADATA_DONE"
    TRANSCRIPT_DONE = "TRANSCRIPT_DONE"
    ANALYZED = "ANALYZED"
    FAILED = "FAILED"


class TranscriptStatus(str, Enum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


class JobStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    DONE = "DONE"
    FAILED = "FAILED"
    DLQ = "DLQ"


class JobType(str, Enum):
    FETCH_METADATA = "FETCH_METADATA"
    TRANSCRIPT = "TRANSCRIPT"
    ANALYZE = "ANALYZE"
    BACKFILL = "BACKFILL"
    RETRY = "RETRY"


class Channel(Base):
    __tablename__ = "channels"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    channel_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    handle: Mapped[str | None] = mapped_column(String(128), unique=True)
    display_name: Mapped[str] = mapped_column(String(255))
    category_primary: Mapped[str] = mapped_column(String(100), nullable=False)
    country: Mapped[str] = mapped_column(String(8), default="KR")
    language: Mapped[str] = mapped_column(String(16), default="ko")
    is_interview_heavy: Mapped[bool] = mapped_column(Boolean, default=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)

    videos = relationship("Video", back_populates="channel", cascade="all,delete")
    sync_state = relationship("ChannelSyncState", uselist=False, back_populates="channel", cascade="all,delete")


class ChannelSyncState(Base):
    __tablename__ = "channel_sync_state"

    channel_id: Mapped[int] = mapped_column(ForeignKey("channels.id", ondelete="CASCADE"), primary_key=True)
    last_feed_published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_polled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_success_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    consecutive_failures: Mapped[int] = mapped_column(Integer, default=0)

    channel = relationship("Channel", back_populates="sync_state")


class Video(Base):
    __tablename__ = "videos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    video_id: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)
    channel_id: Mapped[int] = mapped_column(ForeignKey("channels.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str | None] = mapped_column(String(500))
    description: Mapped[str | None] = mapped_column(Text)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    duration_sec: Mapped[int | None] = mapped_column(Integer)
    is_short: Mapped[bool] = mapped_column(Boolean, default=False)
    is_live: Mapped[bool] = mapped_column(Boolean, default=False)
    is_upcoming: Mapped[bool] = mapped_column(Boolean, default=False)
    caption_available: Mapped[bool] = mapped_column(Boolean, default=False)
    view_count: Mapped[int | None] = mapped_column(Integer)
    like_count: Mapped[int | None] = mapped_column(Integer)
    comment_count: Mapped[int | None] = mapped_column(Integer)
    thumbnail_url: Mapped[str | None] = mapped_column(Text)
    source_url: Mapped[str | None] = mapped_column(Text)
    ingest_status: Mapped[IngestStatus] = mapped_column(String(16), default=IngestStatus.NEW)
    transcript_status: Mapped[TranscriptStatus] = mapped_column(String(16), default=TranscriptStatus.SKIPPED)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)

    channel = relationship("Channel", back_populates="videos")


class Transcript(Base):
    __tablename__ = "transcripts"
    __table_args__ = (UniqueConstraint("video_id", "source_type", name="uq_transcript_video_provider"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    video_id: Mapped[int] = mapped_column(ForeignKey("videos.id", ondelete="CASCADE"), nullable=False, index=True)
    source_type: Mapped[str] = mapped_column(String(32), nullable=False)
    language_code: Mapped[str | None] = mapped_column(String(8))
    text_full: Mapped[str] = mapped_column(Text)
    segments_json: Mapped[dict | list] = mapped_column(JSON().with_variant(JSONB, "postgresql"), nullable=False, default=list)
    provider_name: Mapped[str | None] = mapped_column(String(80))
    provider_version: Mapped[str | None] = mapped_column(String(40))
    status: Mapped[TranscriptStatus] = mapped_column(String(16), default=TranscriptStatus.SUCCESS)
    error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class Analysis(Base):
    __tablename__ = "analyses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    video_id: Mapped[int] = mapped_column(ForeignKey("videos.id", ondelete="CASCADE"), nullable=False, unique=True)
    model_provider: Mapped[str] = mapped_column(String(50))
    model_name: Mapped[str] = mapped_column(String(80))
    prompt_version: Mapped[str] = mapped_column(String(40))
    taxonomy_version: Mapped[str] = mapped_column(String(40))
    summary: Mapped[str] = mapped_column(Text)
    topics_json: Mapped[list] = mapped_column(JSON().with_variant(JSONB, "postgresql"), default=list)
    topic_stances_json: Mapped[list] = mapped_column(JSON().with_variant(JSONB, "postgresql"), default=list)
    signals_json: Mapped[list] = mapped_column(JSON().with_variant(JSONB, "postgresql"), default=list)
    mentioned_assets_json: Mapped[list] = mapped_column(JSON().with_variant(JSONB, "postgresql"), default=list)
    risk_flags_json: Mapped[list] = mapped_column(JSON().with_variant(JSONB, "postgresql"), default=list)
    confidence_overall: Mapped[float | None] = mapped_column(Float)
    subject_type: Mapped[str] = mapped_column(String(24), default="channel")
    raw_output_json: Mapped[dict] = mapped_column(JSON().with_variant(JSONB, "postgresql"), default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class ProcessingJob(Base):
    __tablename__ = "processing_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_type: Mapped[str] = mapped_column(String(30))
    entity_type: Mapped[str] = mapped_column(String(30))
    entity_id: Mapped[str] = mapped_column(String(64))
    status: Mapped[JobStatus] = mapped_column(String(16), default=JobStatus.PENDING)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    last_error: Mapped[str | None] = mapped_column(Text)
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    @property
    def is_terminal(self) -> bool:
        return self.status in {JobStatus.DONE, JobStatus.DLQ}
