from __future__ import annotations

from app.services.analysis.analyzer import AnalysisPayload, MockAnalysisProvider


def test_mock_analysis_schema_shape():
    provider = MockAnalysisProvider()
    parsed = provider.analyze("ETF 투자 토픽 분석", "금리와 주식", "연내 조정이 있을 수 있지만, 장기 관점은 낙관적")
    payload: AnalysisPayload = parsed.payload

    assert payload.topics
    assert isinstance(payload.topic_stances, list)
    assert payload.signals
    assert payload.summary
