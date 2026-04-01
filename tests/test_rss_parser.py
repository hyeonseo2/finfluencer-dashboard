from __future__ import annotations

from app.services.ingestion.rss_poller import extract_video_id


class Dummy:
    pass


def test_extract_video_id_from_yt_id_field():
    e = Dummy()
    e.yt_videoid = "abc123"
    e.link = "https://www.youtube.com/watch?v=z"
    assert extract_video_id(e) == "abc123"


def test_extract_video_id_from_link():
    e = Dummy()
    e.link = "https://www.youtube.com/watch?v=videoXYZ123"
    assert extract_video_id(e) == "videoXYZ123"
