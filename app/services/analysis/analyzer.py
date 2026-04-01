from __future__ import annotations

import json
import re
from dataclasses import dataclass

from pydantic import BaseModel, Field

from app.core.config import settings


class Evidence(BaseModel):
    start_sec: int | None = None
    end_sec: int | None = None
    quote_excerpt: str | None = None
    rationale: str | None = None


class TopicStance(BaseModel):
    topic: str
    stance: str
    confidence: float | None = Field(default=None, ge=0, le=1)
    evidence: list[Evidence] = Field(default_factory=list)


class Signal(BaseModel):
    signal: str
    target: str | None = None
    confidence: float | None = Field(default=None, ge=0, le=1)


class AnalysisPayload(BaseModel):
    summary: str
    topics: list[str]
    topic_stances: list[TopicStance]
    signals: list[Signal]
    mentioned_assets: list[str]
    risk_flags: list[str]
    analysis_notes: str | None = None


@dataclass
class ParsedAnalysis:
    model_provider: str
    model_name: str
    prompt_version: str
    taxonomy_version: str
    payload: AnalysisPayload


class IAnalysisProvider:
    def analyze(self, title: str, description: str | None, transcript: str | None) -> ParsedAnalysis:
        raise NotImplementedError


class _TopicHeuristic:
    whitelist_order = ["macro", "real_estate", "stocks", "etf", "crypto", "fx", "bonds", "commodities", "policy", "interest_rate"]

    stance_aliases = {
        "bullish": "positive",
        "positive": "positive",
        "bearish": "negative",
        "negative": "negative",
        "hawkish": "negative",
        "dovish": "positive",
        "neutral": "neutral",
    }

    topic_keywords = {
        "macro": [
            "거시", "macro", "경기", "경제", "물가", "inflation", "긴축", "완화", "실물", "고용", "실업", "소비", "경기", "금리", "경제지표", "실적", "지표", "거시", "시장", "미국",
            "국내", "경기전망", "경기부양", "경기침체", "경기침체", "금융시장", "금융시장", "지수", "브레이크", "중앙은행",
        ],
        "real_estate": [
            "부동산", "아파트", "집", "집값", "매매", "대출", "분양", "주택", "주거", "전세", "보금자리", "청약", "부동산", "시세", "전세사기", "LH", "재개발", "재건축", "오피스텔", "원룸",
        ],
        "stocks": [
            "주식", "stocks", "증시", "kospi", "코스피", "나스닥", "상승", "하락", "시가총액", "삼성", "애플", "테슬라", "종목", "매수", "매도", "급등", "급락", "실적발표", "개장", "종가", "개별주", "거래량", "밸류", "PER",
            "매매", "주가", "주식시장", "포트폴리오", "포트폴리오"
        ],
        "etf": [
            "etf", "상장지수펀드", "인덱스펀드", "배당", "지수", "패시브", "S&P", "나스닥100", "QQQ", "SPY", "TQQQ", "IVV",
        ],
        "crypto": [
            "비트코인", "비트", "코인", "암호화폐", "crypto", "bitcoin", "이더리움", "이더", "알트코인", "도지", "시총", "체인",
        ],
        "fx": [
            "달러", "엔화", "원화", "환율", "외환", "달러", "유로", "파운드", "위안", "금리차", "원달러", "usd", "usd", "eur", "jpy", "forex", "환전",
        ],
        "bonds": [
            "채권", "국채", "회사채", "금리", "수익률", "채권", "디폴트", "크레딧", "수익률곡선", "채권형", "쿠폰", "만기", "국채선물",
        ],
        "commodities": [
            "금", "원유", "금값", "은", "구리", "원자재", "석유", "곡물", "니켈", "구리", "은", "금속", "에너지", "천연가스", "WTI",
        ],
        "policy": [
            "정부", "정책", "세금", "규제", "금리정책", "중앙은행", "금융", "재정", "통화정책", "부동산세", "정부대응", "입법", "세제", "입법안", "법안", "정책성향",
        ],
        "interest_rate": [
            "금리", "fed", "은행 금리", "기준금리", "인하", "인상", "통화정책", "금리인하", "금리상승", "금리동결", "금리결정", "고금리", "저금리", "물가지수"
        ],
    }

    @classmethod
    def normalize_stance(cls, stance: str | None) -> str:
        if not stance:
            return "neutral"
        return cls.stance_aliases.get(str(stance).strip().lower(), "neutral")

    @classmethod
    def normalize_topic(cls, t: str) -> str:
        if t in cls.whitelist_order:
            return t
        return ""

    @classmethod
    def clean_text(cls, text: str | None) -> str:
        if not text:
            return ""
        txt = text.lower()
        # collapse spaces to help substring matches like e.g. 주  립 가
        txt = re.sub(r"\s+", " ", txt)
        return txt

    @classmethod
    def extract_topics(cls, title: str, description: str | None, transcript: str | None, raw_topics: list[str] | None = None) -> list[str]:
        detected: list[str] = []

        if raw_topics:
            for t in raw_topics:
                t = cls.normalize_topic(t.strip())
                if t and t not in detected:
                    detected.append(t)

        if len(detected) == 0:
            text = cls.clean_text(f"{title}. {description or ''} {transcript or ''}")
            for topic in cls.whitelist_order:
                for k in cls.topic_keywords.get(topic, []):
                    if k.lower() in text:
                        detected.append(topic)
                        break

        if not detected:
            # 마지막 fallback: title만으로도 분류가 어렵다면 macro 보수 할당
            detected = ["macro"]

        return detected[:3]

    @classmethod
    def extract_summary_snippet(cls, title: str, description: str | None, transcript: str | None) -> str:
        if transcript:
            text = transcript[:200]
            return f"{text}..." if len(transcript) > 200 else text
        if description:
            text = description[:200]
            return f"{text}..." if len(description) > 200 else text

        return (title or "요약 정보를 수집할 수 없습니다.")[:120]

    @classmethod
    def build_topic_stances(
        cls,
        title: str,
        description: str | None,
        transcript: str | None,
        topics: list[str],
        default_stance: str = "neutral",
    ) -> list[TopicStance]:
        if not topics:
            return []
        out: list[TopicStance] = []
        quote = (transcript or title or description or "").strip()[:160]
        for t in topics:
            out.append(
                TopicStance(
                    topic=t,
                    stance=cls.normalize_stance(default_stance),
                    confidence=0.55,
                    evidence=[
                        Evidence(
                            start_sec=0,
                            end_sec=0,
                            quote_excerpt=quote,
                            rationale="keyword-only fallback",
                        )
                    ],
                )
            )
        return out


class MockAnalysisProvider(IAnalysisProvider):
    """Deterministic, zero-cost fallback provider for local/offline setup."""

    def analyze(self, title: str, description: str | None, transcript: str | None) -> ParsedAnalysis:
        detected_topics = _TopicHeuristic.extract_topics(title=title or "", description=description, transcript=transcript)
        topic_stances = _TopicHeuristic.build_topic_stances(title, description, transcript, detected_topics)
        summary_text = _TopicHeuristic.extract_summary_snippet(title, description, transcript)

        return ParsedAnalysis(
            model_provider="mock",
            model_name="heuristic-v1",
            prompt_version=settings.prompt_version,
            taxonomy_version=settings.taxonomy_version,
            payload=AnalysisPayload(
                summary=summary_text,
                topics=detected_topics,
                topic_stances=topic_stances,
                signals=[Signal(signal="no_actionable_signal", confidence=0.1)],
                mentioned_assets=[],
                risk_flags=["speculative_language"],
                analysis_notes="자동 분석 백업 모드입니다.",
            ),
        )


class OpenAIAnalysisProvider(IAnalysisProvider):
    def analyze(self, title: str, description: str | None, transcript: str | None) -> ParsedAnalysis:
        if not settings.openai_api_key:
            # graceful degrade
            return MockAnalysisProvider().analyze(title, description, transcript)

        import openai  # type: ignore

        system_prompt = open("app/prompts/analysis_system.txt", encoding="utf-8").read().strip()
        user_prompt = f"title: {title}\ndescription: {description or ''}\ntranscript: {transcript or ''}"

        client = openai.OpenAI(api_key=settings.openai_api_key)
        resp = client.chat.completions.create(
            model=settings.openai_model,
            response_format={"type": "json_object"},
            temperature=0.2,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        raw = resp.choices[0].message.content or "{}"
        obj = json.loads(raw)

        # sanitize and backfill topics
        raw_topics = obj.get("topics") or []
        if not isinstance(raw_topics, list):
            raw_topics = []

        detected_topics = _TopicHeuristic.extract_topics(title, description, transcript, raw_topics=[t for t in raw_topics if isinstance(t, str)])

        payload_dict = dict(obj)
        payload_dict["topics"] = detected_topics

        topic_stances_payload = []
        for item in (payload_dict.get("topic_stances") or []):
            try:
                item_obj = TopicStance(**item) if isinstance(item, dict) else item
                if isinstance(item_obj, dict):
                    item_obj = TopicStance(**item_obj)
                item_obj.stance = _TopicHeuristic.normalize_stance(item_obj.stance)
                topic_stances_payload.append(item_obj)
            except Exception:
                continue

        payload_dict["topic_stances"] = topic_stances_payload
        payload = AnalysisPayload(**payload_dict)

        # ensure topic_stances has same order + existing stances where possible
        if not payload.topic_stances:
            payload.topic_stances = _TopicHeuristic.build_topic_stances(title, description, transcript, detected_topics)

        return ParsedAnalysis(
            model_provider="openai",
            model_name=settings.openai_model,
            prompt_version=settings.prompt_version,
            taxonomy_version=settings.taxonomy_version,
            payload=payload,
        )


class GeminiAnalysisProvider(IAnalysisProvider):
    def analyze(self, title: str, description: str | None, transcript: str | None) -> ParsedAnalysis:
        if not settings.gemini_api_key:
            return MockAnalysisProvider().analyze(title, description, transcript)

        import requests  # type: ignore

        system_prompt = open("app/prompts/analysis_system.txt", encoding="utf-8").read().strip()
        user_prompt = (
            f"{system_prompt}\n\n"
            f"title: {title}\ndescription: {description or ''}\ntranscript: {transcript or ''}"
        )

        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{settings.gemini_model}:generateContent?key={settings.gemini_api_key}"
        )
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": user_prompt}
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.2,
                "responseMimeType": "application/json",
            },
        }

        try:
            resp = requests.post(url, json=payload, timeout=90)
            resp.raise_for_status()
            data = resp.json()
            raw = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "{}")
            obj = json.loads(raw)
        except Exception as e:
            obj = {
                "summary": _TopicHeuristic.extract_summary_snippet(title, description, transcript),
                "topics": [],
                "topic_stances": [],
                "signals": [{"signal": "no_actionable_signal", "confidence": 0.1}],
                "mentioned_assets": [],
                "risk_flags": ["speculative_language"],
                "analysis_notes": f"Gemini 호출 실패로 백업 모드 전환: {e}",
            }

        if not isinstance(obj, dict):
            obj = {}

        raw_topics = obj.get("topics") or []
        if not isinstance(raw_topics, list):
            raw_topics = []

        detected_topics = _TopicHeuristic.extract_topics(
            title,
            description,
            transcript,
            raw_topics=[t for t in raw_topics if isinstance(t, str)],
        )

        payload_dict = dict(obj)
        payload_dict["topics"] = detected_topics

        normalized_stances = []
        for item in (payload_dict.get("topic_stances") or []):
            try:
                tobj = TopicStance(**item) if isinstance(item, dict) else item
                if isinstance(tobj, dict):
                    tobj = TopicStance(**tobj)
                tobj.stance = _TopicHeuristic.normalize_stance(tobj.stance)
                if tobj.confidence is None:
                    tobj.confidence = 0.55
                normalized_stances.append(tobj)
            except Exception:
                continue

        payload_dict["topic_stances"] = normalized_stances
        payload = AnalysisPayload(**payload_dict)

        if not payload.topic_stances:
            payload.topic_stances = _TopicHeuristic.build_topic_stances(title, description, transcript, detected_topics)

        return ParsedAnalysis(
            model_provider="gemini",
            model_name=settings.gemini_model,
            prompt_version=settings.prompt_version,
            taxonomy_version=settings.taxonomy_version,
            payload=payload,
        )


def get_analysis_provider():
    if settings.llm_provider == "openai":
        return OpenAIAnalysisProvider()
    if settings.llm_provider == "gemini":
        return GeminiAnalysisProvider()
    return MockAnalysisProvider()
