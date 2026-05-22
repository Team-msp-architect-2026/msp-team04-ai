import json
import re
from typing import Any

from app.schemas.next_recommend import (
    NextRecommendCandidateProgram,
    NextRecommendItem,
    NextRecommendRequest,
    NextRecommendResponse,
)
from app.services.openai_client import generate_next_recommend_json


MAX_MESSAGE_LENGTH = 140
MAX_REASON_LENGTH = 90
MAX_TAG_LENGTH = 12


def generate_next_recommend(
    request: NextRecommendRequest,
) -> NextRecommendResponse:
    prompt = build_prompt(request)
    result_json = generate_next_recommend_json(prompt)

    message = normalize_text(
        result_json.get("message"),
        MAX_MESSAGE_LENGTH,
    )

    items = normalize_items(
        raw_items=result_json.get("items"),
        candidates=request.candidates,
        applied_category=request.applied_program.category,
    )

    if not message:
        message = build_default_message(request)

    if len(items) != len(request.candidates):
        raise ValueError("Next recommend response does not include all candidate programs.")

    return NextRecommendResponse(
        message=message,
        items=items,
        source="OPENAI",
    )


def build_prompt(request: NextRecommendRequest) -> str:
    payload = {
        "child": {
            "age": request.child.age,
            "concerns": request.child.concerns,
        },
        "appliedProgram": {
            "programId": request.applied_program.program_id,
            "title": request.applied_program.title,
            "category": request.applied_program.category,
            "description": request.applied_program.description or "",
            "classTime": request.applied_program.class_time,
            "price": request.applied_program.price,
            "isFree": request.applied_program.is_free,
            "ratingAvg": request.applied_program.rating_avg,
        },
        "candidates": [
            {
                "programId": candidate.program_id,
                "title": candidate.title,
                "category": candidate.category,
                "description": candidate.description or "",
                "classTime": candidate.class_time,
                "price": candidate.price,
                "isFree": candidate.is_free,
                "ratingAvg": candidate.rating_avg,
                "reasonBasis": candidate.reason_basis or "",
            }
            for candidate in request.candidates
        ],
    }

    return f"""
너는 MoMent 신청 완료 화면에 표시할 AI 다음 추천 설명 생성기다.

목표:
- 이미 백엔드가 선택한 다음 추천 후보를 부모가 쉽게 이해하도록 설명한다.
- 다음 추천 후보를 새로 만들거나 순서를 바꾸지 않는다.
- 추천 점수나 후보 산출은 하지 않는다.
- 신청 완료 프로그램과 다음 추천 후보의 관계를 자연스럽게 설명한다.
- 자녀 관심사, 신청 완료 프로그램, 후보 프로그램 정보, reasonBasis만 사용한다.
- 입력 데이터에 없는 기관명, 혜택명, 후기, 의학적 효과, 발달 효과를 지어내지 않는다.
- 확정적인 효과 표현은 피하고, “도움이 될 수 있어요”, “함께 비교해보면 좋아요”처럼 부드럽게 작성한다.
- message는 전체 다음 추천 안내 문장이다.
- explainMessage는 후보별 한 줄 추천 설명이다.
- highlightTag는 12자 이내 짧은 키워드다.
- message는 140자 이내로 작성한다.
- explainMessage는 각 90자 이내로 작성한다.
- 반드시 입력받은 모든 programId에 대해 items를 반환한다.
- 반드시 JSON만 반환한다.

출력 JSON 형식:
{{
  "message": "신청한 수업과 함께 보면 좋은 다음 프로그램을 정리했어요.",
  "items": [
    {{
      "programId": 7,
      "title": "창의 미술 탐험",
      "explainMessage": "수학 수업과 함께 창의 미술 활동을 병행하면 아이가 다른 방식으로 표현해볼 수 있어요.",
      "highlightTag": "창의 확장"
    }}
  ]
}}

입력 데이터:
{json.dumps(payload, ensure_ascii=False)}
""".strip()


def normalize_items(
    raw_items: Any,
    candidates: list[NextRecommendCandidateProgram],
    applied_category: str | None,
) -> list[NextRecommendItem]:
    if not isinstance(raw_items, list):
        raise ValueError("Next recommend response must contain items array.")

    candidate_map = {candidate.program_id: candidate for candidate in candidates}
    seen: set[int] = set()
    items: list[NextRecommendItem] = []

    for item in raw_items:
        if not isinstance(item, dict):
            continue

        program_id = item.get("programId")
        title = normalize_text(item.get("title"), 60)
        explain_message = normalize_text(item.get("explainMessage"), MAX_REASON_LENGTH)
        highlight_tag = normalize_text(item.get("highlightTag"), MAX_TAG_LENGTH)

        try:
            program_id = int(program_id)
        except (TypeError, ValueError):
            continue

        if program_id not in candidate_map:
            continue

        if program_id in seen:
            continue

        candidate = candidate_map[program_id]

        if not title:
            title = candidate.title

        if not explain_message:
            explain_message = build_default_candidate_reason(
                candidate=candidate,
                applied_category=applied_category,
            )

        if not highlight_tag:
            highlight_tag = build_default_tag(candidate)

        seen.add(program_id)
        items.append(
            NextRecommendItem(
                program_id=program_id,
                title=title,
                explain_message=explain_message,
                highlight_tag=highlight_tag,
            )
        )

    return items


def normalize_text(value: Any, max_length: int) -> str:
    if not isinstance(value, str):
        return ""

    normalized = value.replace("\u00a0", " ").replace("\u200b", "")
    normalized = " ".join(normalized.split())

    replacements = {
        "표현력 향상에도움을": "표현력 향상에 도움을",
        "향상에도움을": "향상에 도움을",
        "에도움을": "에 도움을",
        "함께로봇을만들며": "함께 로봇을 만들며",
        "함께로봇을": "함께 로봇을",
        "로봇을만들며": "로봇을 만들며",
        "로봇을만들": "로봇을 만들",
        "코딩과로봇만들기": "코딩과 로봇 만들기",
        "코딩과 로봇만들기": "코딩과 로봇 만들기",
        "로봇만들기": "로봇 만들기",
        "코딩과로봇": "코딩과 로봇",
        "코딩과로봇 활동": "코딩과 로봇 활동",
        "미술과음악": "미술과 음악",
        "미술과음악 활동": "미술과 음악 활동",
        "수학과과학": "수학과 과학",
        "수학과과학 활동": "수학과 과학 활동",
        "입니 다": "입니다",
        "합니 다": "합니다",
        "좋 아요": "좋아요",
        "있 어요": "있어요",
        "없 어요": "없어요",
        "되 어요": "돼요",
        "프 로그램": "프로그램",
        "프로 그램": "프로그램",
        "수 업": "수업",
        "추 천": "추천",
        "다 음": "다음",
        "신 청": "신청",
        "완 료": "완료",
        "함 께": "함께",
        "비 교": "비교",
        "창 의": "창의",
        "표 현": "표현",
        "학 습": "학습",
        "돌 봄": "돌봄",
        "체 험": "체험",
        "관 심": "관심",
        "자 녀": "자녀",
        "아이 에게": "아이에게",
        "도움 이": "도움이",
        "될 수 있어요": "될 수 있어요",
    }

    for source, target in replacements.items():
        normalized = normalized.replace(source, target)

    normalized = re.sub(
        r"(?<=[가-힣])\s+(?=(이|가|은|는|을|를|와|과|도|만|의|에|로|으로|에서|에게|부터|까지|처럼|보다))",
        "",
        normalized,
    )

    normalized = " ".join(normalized.split())

    if len(normalized) > max_length:
        normalized = normalized[:max_length].rstrip()

    return normalized


def build_default_message(request: NextRecommendRequest) -> str:
    applied_title = request.applied_program.title or "신청한 프로그램"

    return f"{applied_title} 신청 후 함께 비교해볼 만한 다음 추천 프로그램을 정리했어요."


def build_default_candidate_reason(
    candidate: NextRecommendCandidateProgram,
    applied_category: str | None,
) -> str:
    if applied_category:
        return f"{applied_category} 수업과 함께 {candidate.title}도 비교해보면 좋아요."

    return f"{candidate.title}도 아이 조건과 함께 비교해볼 만한 프로그램이에요."


def build_default_tag(candidate: NextRecommendCandidateProgram) -> str:
    if candidate.category:
        return candidate.category[:MAX_TAG_LENGTH]

    return "다음 추천"
