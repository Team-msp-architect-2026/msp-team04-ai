import json
import re
from typing import Any

from app.schemas.review_keywords import (
    ReviewKeywordsRequest,
    ReviewKeywordsResponse,
)
from app.services.openai_client import generate_review_keywords_json


MAX_POSITIVE_KEYWORD_COUNT = 5
MAX_NEGATIVE_KEYWORD_COUNT = 3
MAX_KEYWORD_LENGTH = 20
MAX_SUMMARY_LENGTH = 120


def generate_review_keywords(
    request: ReviewKeywordsRequest,
) -> ReviewKeywordsResponse:
    prompt = build_prompt(request)
    result_json = generate_review_keywords_json(prompt)

    positive_keywords = normalize_keyword_list(
        result_json.get("positiveKeywords") or result_json.get("positive_keywords"),
        request.stats.positive_keywords,
        MAX_POSITIVE_KEYWORD_COUNT,
    )

    negative_keywords = normalize_keyword_list(
        result_json.get("negativeKeywords") or result_json.get("negative_keywords"),
        request.stats.negative_keywords,
        MAX_NEGATIVE_KEYWORD_COUNT,
    )

    if not positive_keywords:
        positive_keywords = normalize_keyword_list(
            request.stats.positive_keywords,
            request.stats.positive_keywords,
            MAX_POSITIVE_KEYWORD_COUNT,
        )

    if not negative_keywords:
        negative_keywords = normalize_keyword_list(
            request.stats.negative_keywords,
            request.stats.negative_keywords,
            MAX_NEGATIVE_KEYWORD_COUNT,
        )

    summary = build_default_summary(request, positive_keywords, negative_keywords)

    return ReviewKeywordsResponse(
        positive_keywords=positive_keywords,
        negative_keywords=negative_keywords,
        summary=summary,
        source="OPENAI",
    )


def build_prompt(request: ReviewKeywordsRequest) -> str:
    payload = {
        "program": {
            "programId": request.program.program_id,
            "title": request.program.title,
            "category": request.program.category,
            "ratingAvg": request.program.rating_avg,
            "reviewCount": request.program.review_count,
        },
        "stats": {
            "reviewCount": request.stats.review_count,
            "ratingAverage": request.stats.rating_average,
            "ratingDistribution": request.stats.rating_distribution,
            "positiveKeywords": request.stats.positive_keywords,
            "negativeKeywords": request.stats.negative_keywords,
            "reviewTexts": request.stats.review_texts[:20],
        },
    }

    return f"""
너는 MoMent 프로그램 상세 후기 탭의 AI 후기 키워드 분석 생성기다.

목표:
- 백엔드가 후기 원문과 별점 분포를 분석해서 추출한 긍정/부정 키워드 후보를 바탕으로 부모가 이해하기 쉬운 요약 문구를 만든다.
- 후기 원문과 별점 분포에 없는 내용을 지어내지 않는다.
- positiveKeywords와 negativeKeywords는 반드시 입력으로 받은 후보 안에서만 선택한다.
- 새로운 키워드를 invent 하지 않는다.
- 부정 키워드 후보가 없으면 negativeKeywords는 빈 배열로 둔다.
- summary는 프로그램 상세 후기 탭에 표시될 짧은 문장으로 작성한다.
- summary는 120자 이내 한국어 문장으로 작성한다.
- 과장된 표현, 확정적 의료/발달 효과 표현, 제공되지 않은 기관명/교사명은 쓰지 않는다.
- 반드시 JSON만 반환한다.

출력 JSON 형식:
{{
  "positiveKeywords": ["선생님 친절", "소규모 수업", "만족도 높음"],
  "negativeKeywords": [],
  "summary": "후기에서 선생님의 친절함과 소규모 케어에 대한 만족도가 높게 나타났어요."
}}

입력 데이터:
{json.dumps(payload, ensure_ascii=False)}
""".strip()


def normalize_keyword_list(
    raw_keywords: Any,
    allowed_keywords: list[str],
    limit: int,
) -> list[str]:
    if not isinstance(raw_keywords, list):
        return []

    allowed_map = {
        normalize_keyword(keyword).replace(" ", ""): normalize_keyword(keyword)
        for keyword in allowed_keywords
        if normalize_keyword(keyword)
    }

    if not allowed_map:
        return []

    seen: set[str] = set()
    normalized_keywords: list[str] = []

    for item in raw_keywords:
        keyword = normalize_keyword(item)
        key = keyword.replace(" ", "")

        if not keyword or key not in allowed_map or key in seen:
            continue

        seen.add(key)
        normalized_keywords.append(allowed_map[key])

        if len(normalized_keywords) >= limit:
            break

    return normalized_keywords


def normalize_keyword(value: Any) -> str:
    if not isinstance(value, str):
        return ""

    normalized = value.replace("\u00a0", " ").replace("\u200b", "")
    normalized = " ".join(normalized.split())
    normalized = re.sub(r"[^0-9A-Za-z가-힣\s]", "", normalized)
    normalized = " ".join(normalized.split())

    if len(normalized) > MAX_KEYWORD_LENGTH:
        normalized = normalized[:MAX_KEYWORD_LENGTH].rstrip()

    return normalized


def normalize_summary(value: Any) -> str:
    if not isinstance(value, str):
        return ""

    normalized = value.replace("\u00a0", " ").replace("\u200b", "")
    normalized = " ".join(normalized.split())

    replacements = {
        "후 기": "후기",
        "키 워드": "키워드",
        "선 생님": "선생님",
        "친 절": "친절",
        "소 규모": "소규모",
        "수 업": "수업",
        "만 족도": "만족도",
        "피 드백": "피드백",
        "온 라인": "온라인",
        "프 로젝트": "프로젝트",
        "집 중": "집중",
        "좋 아요": "좋아요",
        "높 아요": "높아요",
        "나타 났어요": "나타났어요",
        "보 여요": "보여요",
    }

    for source, target in replacements.items():
        normalized = normalized.replace(source, target)

    normalized = re.sub(
        r"(?<=[가-힣])\s+(?=(이|가|은|는|을|를|와|과|도|만|의|에|로|으로|에서|에게|부터|까지|처럼|보다))",
        "",
        normalized,
    )

    normalized = " ".join(normalized.split())

    spacing_replacements = {
        "아이의만족도": "아이의 만족도",
        "아이의흥미": "아이의 흥미",
        "아이의집중": "아이의 집중",
        "아이의참여": "아이의 참여",
        "아이의수업": "아이의 수업",
        "후기의만족도": "후기의 만족도",
        "수업의만족도": "수업의 만족도",
        "프로그램의만족도": "프로그램의 만족도",
    }

    for source, target in spacing_replacements.items():
        normalized = normalized.replace(source, target)

    normalized = re.sub(
        r"(아이|후기|수업|프로그램)의(?=(만족도|흥미|집중|참여|수업|피드백|완성도|친밀도|반응|경험))",
        r"\\1의 ",
        normalized,
    )

    normalized = " ".join(normalized.split())

    if len(normalized) > MAX_SUMMARY_LENGTH:
        normalized = normalized[:MAX_SUMMARY_LENGTH].rstrip()

    return normalized


def build_default_summary(
    request: ReviewKeywordsRequest,
    positive_keywords: list[str],
    negative_keywords: list[str],
) -> str:
    if request.stats.review_count <= 0:
        return "아직 등록된 후기가 없어 AI 키워드 분석을 준비 중이에요."

    if positive_keywords:
        return "등록된 후기를 기준으로 아이 반응과 수업 만족도가 긍정적으로 나타났어요."

    if negative_keywords:
        joined = ", ".join(negative_keywords[:2])
        return f"후기에서 {joined} 관련 의견도 함께 확인할 수 있어요."

    return "등록된 후기를 바탕으로 전반적인 만족도를 확인할 수 있어요."
