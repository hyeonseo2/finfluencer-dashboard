from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


DISCLAIMER = "본 서비스는 공개된 콘텐츠를 바탕으로 의견을 구조화해 제공하는 정보 서비스이며, 투자 권유 또는 투자자문을 제공하지 않습니다. 투자 판단과 책임은 이용자 본인에게 있습니다."


class ErrorResponse(BaseModel):
    detail: str


class ChannelCreate(BaseModel):
    channel_id: str | None = None
    handle: str | None = None
    display_name: str
    category_primary: str
    country: str = "KR"
    language: str = "ko"
    is_interview_heavy: bool = False
    active: bool = True


class ChannelOut(BaseModel):
    channel_id: str
    channel_avatar_url: str | None = None
    handle: str | None
    display_name: str
    category_primary: str
    country: str
    language: str
    is_interview_heavy: bool
    active: bool

    class Config:
        from_attributes = True


class ResolveHandleIn(BaseModel):
    handle: str


class ResolveHandleOut(BaseModel):
    handle: str
    channel_id: str
    channel_avatar_url: str | None = None
    display_name: str


class VideoOut(BaseModel):
    video_id: str
    title: str | None
    channel: str
    channel_id: str
    channel_avatar_url: str | None = None
    published_at: datetime | None
    source_url: str | None
    summary: str | None = None
    transcript_preview: str | None = None
    thumbnail_url: str | None = None
    topics: list[str] = Field(default_factory=list)
    topic_stances: list[dict[str, Any]] = Field(default_factory=list)
    signals: list[dict[str, Any]] = Field(default_factory=list)
    transcript_status: str
    disclaimer: str = DISCLAIMER

    class Config:
        from_attributes = True


class OpinionCompareItem(BaseModel):
    video_id: str
    channel: str
    title: str
    published_at: datetime | None
    topic: str
    stance: str | None
    confidence: float | None
    evidence_excerpt: str | None
    source_url: str | None


class TranscriptStatusOut(BaseModel):
    source_type: str
    status: str
    provider_name: str | None
    provider_version: str | None
    language_code: str | None
    updated_at: datetime | None


class JobOut(BaseModel):
    id: int
    job_type: str
    entity_type: str
    entity_id: str
    status: str
    attempts: int
    last_error: str | None
    scheduled_at: datetime
    started_at: datetime | None
    finished_at: datetime | None
