"""initial schema

Revision ID: 001
Revises:
Create initial database tables for MVP.
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "channels",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("channel_id", sa.String(64), nullable=False, unique=True),
        sa.Column("handle", sa.String(128), nullable=True, unique=True),
        sa.Column("display_name", sa.String(255), nullable=False),
        sa.Column("category_primary", sa.String(100), nullable=False),
        sa.Column("country", sa.String(8), nullable=False, server_default="KR"),
        sa.Column("language", sa.String(16), nullable=False, server_default="ko"),
        sa.Column("is_interview_heavy", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "channel_sync_state",
        sa.Column("channel_id", sa.Integer, sa.ForeignKey("channels.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("last_feed_published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_polled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_success_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.Text, nullable=True),
        sa.Column("consecutive_failures", sa.Integer, nullable=False, server_default="0"),
    )

    op.create_table(
        "videos",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("video_id", sa.String(32), nullable=False, unique=True),
        sa.Column("channel_id", sa.Integer, sa.ForeignKey("channels.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(500), nullable=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_sec", sa.Integer, nullable=True),
        sa.Column("is_short", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("is_live", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("is_upcoming", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("caption_available", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("view_count", sa.Integer, nullable=True),
        sa.Column("like_count", sa.Integer, nullable=True),
        sa.Column("comment_count", sa.Integer, nullable=True),
        sa.Column("thumbnail_url", sa.Text, nullable=True),
        sa.Column("source_url", sa.Text, nullable=True),
        sa.Column("ingest_status", sa.String(16), nullable=False, server_default="NEW"),
        sa.Column("transcript_status", sa.String(16), nullable=False, server_default="SKIPPED"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_videos_video_id", "videos", ["video_id"])
    op.create_index("ix_videos_channel_id", "videos", ["channel_id"])
    op.create_index("ix_videos_published_at", "videos", ["published_at"])

    op.create_table(
        "transcripts",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("video_id", sa.Integer, sa.ForeignKey("videos.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source_type", sa.String(32), nullable=False),
        sa.Column("language_code", sa.String(8), nullable=True),
        sa.Column("text_full", sa.Text, nullable=False),
        sa.Column("segments_json", sa.JSON, nullable=False),
        sa.Column("provider_name", sa.String(80), nullable=True),
        sa.Column("provider_version", sa.String(40), nullable=True),
        sa.Column("status", sa.String(16), nullable=False, server_default="SUCCESS"),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("video_id", "source_type", name="uq_transcript_video_provider"),
    )

    op.create_table(
        "analyses",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("video_id", sa.Integer, sa.ForeignKey("videos.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("model_provider", sa.String(50), nullable=False),
        sa.Column("model_name", sa.String(80), nullable=False),
        sa.Column("prompt_version", sa.String(40), nullable=False),
        sa.Column("taxonomy_version", sa.String(40), nullable=False),
        sa.Column("summary", sa.Text, nullable=False),
        sa.Column("topics_json", sa.JSON, nullable=False),
        sa.Column("topic_stances_json", sa.JSON, nullable=False),
        sa.Column("signals_json", sa.JSON, nullable=False),
        sa.Column("mentioned_assets_json", sa.JSON, nullable=False),
        sa.Column("risk_flags_json", sa.JSON, nullable=False),
        sa.Column("confidence_overall", sa.Float, nullable=True),
        sa.Column("subject_type", sa.String(24), nullable=False, server_default="channel"),
        sa.Column("raw_output_json", sa.JSON, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_analyses_created_at", "analyses", ["created_at"])

    op.create_table(
        "processing_jobs",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("job_type", sa.String(30), nullable=False),
        sa.Column("entity_type", sa.String(30), nullable=False),
        sa.Column("entity_id", sa.String(64), nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="PENDING"),
        sa.Column("attempts", sa.Integer, nullable=False, server_default="0"),
        sa.Column("last_error", sa.Text, nullable=True),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_processing_jobs_status", "processing_jobs", ["status"])


def downgrade() -> None:
    op.drop_table("processing_jobs")
    op.drop_table("analyses")
    op.drop_table("transcripts")
    op.drop_table("videos")
    op.drop_table("channel_sync_state")
    op.drop_table("channels")
