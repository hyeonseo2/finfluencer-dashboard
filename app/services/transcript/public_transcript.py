from __future__ import annotations

from app.services.transcript.interfaces import ITranscriptProvider, TranscriptResult, TranscriptSegment


class PublicTranscriptProvider(ITranscriptProvider):
    """Attempt to use public transcript/caption only."""

    provider_name = "public_transcript"
    provider_version = "v1"

    def _to_result(self, transcript: list[dict], language: str = "unknown") -> TranscriptResult:
        segments = [
            TranscriptSegment(
                start_sec=float(s.get("start", 0.0)),
                end_sec=float(s.get("start", 0.0)) + float(s.get("duration", 0.0)),
                text=str(s.get("text", "")).strip(),
            )
            for s in transcript
        ]
        text = " ".join((s.text or "") for s in segments).strip()
        if not text:
            raise RuntimeError("public transcript empty")
        return TranscriptResult(
            text=text,
            language_code=language,
            provider_name=self.provider_name,
            provider_version=self.provider_version,
            segments=segments,
        )

    def get_transcript(self, video_id: str) -> TranscriptResult:
        try:
            from youtube_transcript_api import YouTubeTranscriptApi  # type: ignore
        except Exception as e:
            raise RuntimeError(f"youtube_transcript_api not available: {e}")

        errors: list[str] = []

        # Try preferred languages explicitly first.
        for lang in ["ko", "en"]:
            try:
                transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=[lang])
                return self._to_result(transcript, language=lang)
            except Exception as e:
                errors.append(f"{lang}: {e}")

        # fallback: let library pick one available transcript language
        try:
            transcript = YouTubeTranscriptApi.get_transcript(video_id)
            return self._to_result(transcript, language="auto")
        except Exception as e:
            errors.append(f"auto: {e}")

        raise RuntimeError("public transcript unavailable; " + "; ".join(errors))
