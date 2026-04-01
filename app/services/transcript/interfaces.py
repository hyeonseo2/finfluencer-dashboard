from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass
class TranscriptSegment:
    start_sec: float
    end_sec: float
    text: str


@dataclass
class TranscriptResult:
    text: str
    language_code: str
    provider_name: str
    provider_version: str
    segments: list[TranscriptSegment]


class ITranscriptProvider(Protocol):
    provider_name: str
    provider_version: str

    def get_transcript(self, video_id: str) -> TranscriptResult: ...
