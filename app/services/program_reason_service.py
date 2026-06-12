import json
import re
from typing import Any

from app.schemas.program_reason import (
    ProgramReasonProgram,
    ProgramReasonRequest,
    ProgramReasonResponse,
)
from app.services.openai_client import generate_program_reason_json


MAX_REASON_COUNT = 4
MAX_REASON_LENGTH = 90


def generate_program_reason(
    request: ProgramReasonRequest,
) -> ProgramReasonResponse:
    prompt = build_prompt(request)
    result_json = generate_program_reason_json(prompt)

    reason_list = normalize_reason_list(result_json, request)

    if not reason_list:
        reason_list = build_default_reasons(request)

    return ProgramReasonResponse(
        match_score=request.score.match_score,
        reason_list=reason_list,
        source="OPENAI",
    )


def build_prompt(request: ProgramReasonRequest) -> str:
    preference_payload = None

    if request.preference is not None:
        preference_payload = {
            "region": request.preference.region,
            "monthlyBudget": request.preference.monthly_budget,
            "transportType": request.preference.transport_type,
            "moveTime": request.preference.move_time,
            "onlinePreference": request.preference.online_preference,
            "classType": request.preference.class_type,
        }

    payload = {
        "child": {
            "age": request.child.age,
            "concerns": request.child.concerns,
        },
        "preference": preference_payload,
        "program": {
            "programId": request.program.program_id,
            "title": request.program.title,
            "category": request.program.category,
            "description": request.program.description or "",
            "institutionName": request.program.institution_name,
            "region": request.program.region,
            "price": request.program.price,
            "isFree": request.program.is_free,
            "classType": request.program.class_type,
            "targetAgeMin": request.program.target_age_min,
            "targetAgeMax": request.program.target_age_max,
            "ratingAvg": request.program.rating_avg,
            "reviewCount": request.program.review_count,
            "tags": request.program.tags,
        },
        "score": {
            "matchScore": request.score.match_score,
            "reasonCodes": request.score.reason_codes,
            "scoreBreakdown": request.score.score_breakdown,
        },
    }

    return f"""
너는 MoMent 프로그램 상세 화면의 AI 추천 이유 생성기다.

목표:
- 백엔드가 전달한 child, program, score 정보를 바탕으로 부모가 이해하기 쉬운 추천 이유를 만든다.
- preference가 제공된 경우에만 보호자 선호 조건을 추가 참고한다.
- preference가 null이어도 자녀 나이, 관심사, 프로그램 제목/설명/태그/대상연령/비용 정보를 기준으로 추천 이유를 만든다.
- 추천 점수와 후보는 새로 계산하지 않는다.
- 프로그램 정보, 자녀 나이, 관심사, 백엔드 점수 근거만 사용한다.
- 제공되지 않은 기관명, 혜택명, 후기 내용, 수업 내용을 지어내지 않는다.
- 부모가 프로그램 상세 화면에서 바로 이해할 수 있도록 짧고 구체적인 문장으로 작성한다.
- reasonList는 2개 이상 4개 이하로 작성한다.
- 각 문장은 90자 이내로 작성한다.
- 문체는 한국어, 부모 친화적이고 따뜻하게 작성한다.
- 반드시 JSON만 반환한다.

reasonCodes 의미:
- DISTANCE_CLOSE: 위치 또는 이동 부담이 조건에 잘 맞음
- BUDGET_FIT: 예산 조건에 잘 맞음
- AGE_FIT: 자녀 연령 조건에 잘 맞음
- KEYWORD_MATCH: 자녀 관심사나 고민 키워드와 잘 맞음
- CLASS_TYPE_MATCH: 선호 수업 방식과 잘 맞음
- RECRUITING_OPEN: 현재 신청 가능한 모집 상태
- HIGH_RATING: 평점/후기 만족도가 높음

출력 JSON 형식:
{{
  "reasonList": [
    "아이의 관심사와 프로그램 태그가 잘 맞아 흥미롭게 시작하기 좋아요.",
    "현재 모집 중이라 조건이 맞으면 바로 신청을 검토할 수 있어요."
  ]
}}

입력 데이터:
{json.dumps(payload, ensure_ascii=False)}
""".strip()


def normalize_reason_list(
    result_json: dict[str, Any],
    request: ProgramReasonRequest,
) -> list[str]:
    raw_reasons = result_json.get("reasonList")

    if raw_reasons is None:
        raw_reasons = result_json.get("reasons")

    if not isinstance(raw_reasons, list):
        return []

    seen: set[str] = set()
    reasons: list[str] = []

    for item in raw_reasons:
        if isinstance(item, dict):
            value = item.get("reason") or item.get("text") or item.get("content")
        else:
            value = item

        normalized = normalize_text(value, MAX_REASON_LENGTH)

        if not normalized:
            continue

        key = normalized.replace(" ", "")

        if key in seen:
            continue

        seen.add(key)
        reasons.append(normalized)

        if len(reasons) >= MAX_REASON_COUNT:
            break

    return reasons


def build_default_reasons(request: ProgramReasonRequest) -> list[str]:
    program = request.program
    reason_codes = set(request.score.reason_codes or [])
    reasons: list[str] = []

    if "AGE_FIT" in reason_codes:
        reasons.append("자녀 연령 조건과 프로그램 대상 연령이 잘 맞아 참여하기 좋아요.")

    if "KEYWORD_MATCH" in reason_codes:
        concerns = ", ".join(request.child.concerns[:2])
        if concerns:
            reasons.append(f"{concerns} 관심사와 프로그램 태그가 잘 맞아 흥미를 이어가기 좋아요.")
        else:
            reasons.append("아이의 관심 키워드와 프로그램 특성이 잘 맞는 편이에요.")

    if "BUDGET_FIT" in reason_codes:
        if bool(program.is_free):
            reasons.append("무료 프로그램이라 비용 부담 없이 시작해볼 수 있어요.")
        else:
            reasons.append("보호자가 설정한 예산 조건 안에서 검토하기 좋은 프로그램이에요.")

    if "HIGH_RATING" in reason_codes:
        reasons.append("평점과 후기 수를 함께 봤을 때 만족도 기준에서 비교해볼 만해요.")

    if "RECRUITING_OPEN" in reason_codes:
        reasons.append("현재 모집 중이라 조건이 맞으면 바로 신청을 검토할 수 있어요.")

    if not reasons:
        concerns = ", ".join(request.child.concerns[:2])
        title = normalize_text(program.title, 30) or "이 프로그램"

        if concerns:
            reasons.append(f"{concerns} 관심사를 가진 아이가 체험해보기 좋은 프로그램이에요.")

        if bool(program.is_free):
            reasons.append("무료로 참여할 수 있어 비용 부담 없이 경험해볼 수 있어요.")

        if program.tags:
            tags = ", ".join(program.tags[:2])
            reasons.append(f"{tags} 특성을 가진 프로그램이라 아이가 흥미를 느끼기 좋아요.")

        if not reasons:
            reasons.append(f"{title}은 아이 정보와 프로그램 내용을 기준으로 검토할 만한 프로그램이에요.")

    return reasons[:MAX_REASON_COUNT]


def normalize_text(value: Any, max_length: int) -> str:
    if not isinstance(value, str):
        return ""

    normalized = value.replace("\u00a0", " ").replace("\u200b", "")
    normalized = " ".join(normalized.split())

    replacements = {
        "입니 다": "입니다",
        "합니 다": "합니다",
        "좋 아요": "좋아요",
        "맞 아요": "맞아요",
        "있 어요": "있어요",
        "없 어요": "없어요",
        "되 어요": "돼요",
        "수 업": "수업",
        "프 로그램": "프로그램",
        "프로 그램": "프로그램",
        "코 딩": "코딩",
        "미 술": "미술",
        "체 험": "체험",
        "돌 봄": "돌봄",
        "입 문": "입문",
        "기 초": "기초",
        "학 습": "학습",
        "창 의": "창의",
        "활 동": "활동",
        "발 달": "발달",
        "맞 춤": "맞춤",
        "추 천": "추천",
        "관 심": "관심",
        "조 건": "조건",
        "연 령": "연령",
        "평 점": "평점",
        "후 기": "후기",
        "모 집": "모집",
        "신 청": "신청",
        "하 기": "하기",
        "되 기": "되기",
        "시 작": "시작",
        "참 여": "참여",
        "선 택": "선택",
        "비 교": "비교",
        "기 준": "기준",
        "으 로": "으로",
        "으 며": "으며",
        "하 는": "하는",
        "있 는": "있는",
        "없 는": "없는",
        "시작 할": "시작할",
        "참여 할": "참여할",
        "신청 할": "신청할",
        "검토 할": "검토할",
    }

    for source, target in replacements.items():
        normalized = normalized.replace(source, target)

    normalized = re.sub(
        r"(?<=[가-힣])\s+(?=(이|가|은|는|을|를|와|과|도|만|의|에|로|으로|에서|에게|부터|까지|처럼|보다))",
        "",
        normalized,
    )

    normalized = " ".join(normalized.split())

    normalized = normalized.replace("참여가능합니다", "참여 가능합니다")
    normalized = normalized.replace("참여 가능 합니다", "참여 가능합니다")
    normalized = normalized.replace("신청가능합니다", "신청 가능합니다")
    normalized = normalized.replace("신청 가능 합니다", "신청 가능합니다")
    normalized = normalized.replace("조건을기준으로", "조건을 기준으로")
    normalized = normalized.replace("기준으 로", "기준으로")
    normalized = normalized.replace("비용 으로", "비용으로")
    normalized = normalized.replace("부담  없이", "부담 없이")

    normalized = " ".join(normalized.split())

    if len(normalized) > max_length:
        normalized = normalized[:max_length].rstrip()

    return normalized
