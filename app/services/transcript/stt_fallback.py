from __future__ import annotations

from dataclasses import dataclass

from app.core.config import settings
from app.services.transcript.interfaces import ITranscriptProvider, TranscriptResult, TranscriptSegment


class FallbackTranscriptProvider(ITranscriptProvider):
    """Fallback STT adapter.

    This mock implementation expects pre-generated caption text in a shared cache or object storage.
    In production this is where Whisper API / faster-whisper pipeline should be implemented.
    """

    provider_name = "stt_fallback"
    provider_version = "v1"

    def get_transcript(self, video_id: str) -> TranscriptResult:
        if not settings.stt_enabled:
            raise RuntimeError("STT disabled by config")

        # Minimal deterministic fallback.
        # Keep behavior predictable for MVP and CI: we return a soft-failed placeholder
        # only for very short videos to avoid expensive processing.
        text = ""
        if len(video_id) % 2 == 0:
            text = ""
        if not text:
            raise RuntimeError("STT not implemented in MVP runtime; set up transcriber worker")

        segments = [TranscriptSegment(start_sec=0.0, end_sec=3.0, text=text)]
        return TranscriptResult(
            text=text,
            language_code="ko",
            provider_name=self.provider_name,
            provider_version=self.provider_version,
            segments=segments,
        )
