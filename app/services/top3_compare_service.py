import json
import re
from typing import Any

from app.schemas.top3_compare import (
    Top3CompareItem,
    Top3CompareProgram,
    Top3CompareRequest,
    Top3CompareResponse,
)
from app.services.openai_client import generate_top3_compare_json


MAX_REASON_LENGTH = 80
MAX_SUMMARY_LENGTH = 180
MAX_TAG_LENGTH = 12


def generate_top3_compare(
    request: Top3CompareRequest,
) -> Top3CompareResponse:
    prompt = build_prompt(request)
    result_json = generate_top3_compare_json(prompt)

    common_summary = normalize_text(
        result_json.get("commonSummary"),
        max_length=MAX_SUMMARY_LENGTH,
    )

    items = normalize_items(
        raw_items=result_json.get("items"),
        programs=request.programs,
    )

    if not common_summary:
        common_summary = build_default_common_summary(request.programs)

    if len(items) != len(request.programs):
        raise ValueError("Top3 compare response does not include all programs.")

    return Top3CompareResponse(
        common_summary=common_summary,
        items=items,
        source="OPENAI",
    )


def build_prompt(request: Top3CompareRequest) -> str:
    payload = {
        "child": {
            "age": request.child.age,
            "concerns": request.child.concerns,
        },
        "preference": {
            "region": request.preference.region,
            "monthlyBudget": request.preference.monthly_budget,
            "transportType": request.preference.transport_type,
            "moveTime": request.preference.move_time,
            "onlinePreference": request.preference.online_preference,
            "classType": request.preference.class_type,
        },
        "programs": [
            {
                "programId": program.program_id,
                "title": program.title,
                "category": program.category,
                "description": program.description or "",
                "region": program.region,
                "price": program.price,
                "isFree": program.is_free,
                "classType": program.class_type,
                "ratingAvg": program.rating_avg,
                "reviewCount": program.review_count,
                "rankNo": program.rank_no,
                "totalScore": program.total_score,
                "recommendReason": program.recommend_reason or "",
                "scoreBreakdown": program.score_breakdown,
            }
            for program in request.programs
        ],
    }

    return f"""
너는 MoMent의 AI TOP3 비교 추천 설명 생성기다.

목표:
- 이미 백엔드 추천 엔진이 선정한 TOP3 프로그램을 부모가 쉽게 비교할 수 있도록 설명한다.
- 추천 후보를 새로 만들거나 순위를 바꾸지 않는다.
- totalScore, scoreBreakdown, recommendReason, 프로그램 정보, 자녀 관심사, 선호 조건만 사용한다.
- 제공되지 않은 기관명, 혜택명, 수업 내용, 후기 내용을 지어내지 않는다.
- 추천 점수는 새로 계산하지 않는다.
- 각 프로그램마다 부모가 바로 이해할 수 있는 한 줄 추천 이유를 만든다.
- 전체 TOP3를 함께 비교하는 공통 요약 문장을 만든다.
- 문체는 한국어, 부모 친화적이고 따뜻하게 작성한다.
- commonSummary는 180자 이내로 작성한다.
- oneLineReason은 각 80자 이내로 작성한다.
- highlightTag는 12자 이내의 짧은 키워드로 작성한다.
- 반드시 입력받은 모든 programId에 대해 items를 반환한다.
- 반드시 JSON만 반환한다.

출력 JSON 형식:
{{
  "commonSummary": "세 프로그램 모두 아이의 관심사와 보호자 조건을 기준으로 비교했을 때 선택지가 뚜렷합니다.",
  "items": [
    {{
      "programId": 1,
      "oneLineReason": "무료 수업이면서 연령과 관심 키워드가 잘 맞아 부담 없이 시작하기 좋아요.",
      "highlightTag": "부담 적음"
    }}
  ]
}}

입력 데이터:
{json.dumps(payload, ensure_ascii=False)}
""".strip()


def normalize_items(
    raw_items: Any,
    programs: list[Top3CompareProgram],
) -> list[Top3CompareItem]:
    if not isinstance(raw_items, list):
        raise ValueError("Top3 compare response must contain items array.")

    program_ids = {program.program_id for program in programs}
    seen: set[int] = set()
    items: list[Top3CompareItem] = []

    for item in raw_items:
        if not isinstance(item, dict):
            continue

        program_id = item.get("programId")
        one_line_reason = normalize_text(
            item.get("oneLineReason"),
            max_length=MAX_REASON_LENGTH,
        )
        highlight_tag = normalize_text(
            item.get("highlightTag"),
            max_length=MAX_TAG_LENGTH,
        )

        try:
            program_id = int(program_id)
        except (TypeError, ValueError):
            continue

        if program_id not in program_ids:
            continue

        if program_id in seen:
            continue

        if not one_line_reason:
            continue

        if not highlight_tag:
            highlight_tag = "맞춤 추천"

        seen.add(program_id)
        items.append(
            Top3CompareItem(
                program_id=program_id,
                one_line_reason=one_line_reason,
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
        "참여 가능합니다": "참여 가능합니다",
        "참여가능합니다": "참여 가능합니다",
        "조건을기준으로": "조건을 기준으로",
        "시작 할": "시작할",
        "참여 할": "참여할",
        "선택 할": "선택할",
        "비교 할": "비교할",
    }

    for source, target in replacements.items():
        normalized = normalized.replace(source, target)

    normalized = normalized.replace("참여가능합니다", "참여 가능합니다")
    normalized = normalized.replace("조건을기준으로", "조건을 기준으로")

    normalized = re.sub(
        r"(?<=[가-힣])\s+(?=(이|가|은|는|을|를|와|과|도|만|의|에|로|으로|에서|에게|부터|까지|처럼|보다))",
        "",
        normalized,
    )

    normalized = " ".join(normalized.split())

    normalized = normalized.replace("참여가능합니다", "참여 가능합니다")
    normalized = normalized.replace("참여 가능 합니다", "참여 가능합니다")
    normalized = normalized.replace("조건을기준으로", "조건을 기준으로")
    normalized = normalized.replace("기준으 로", "기준으로")
    normalized = normalized.replace("비용 으로", "비용으로")
    normalized = normalized.replace("부담  없이", "부담 없이")

    normalized = " ".join(normalized.split())

    if len(normalized) > max_length:
        normalized = normalized[:max_length].rstrip()

    return normalized


def build_default_common_summary(programs: list[Top3CompareProgram]) -> str:
    titles = [program.title for program in programs if program.title]

    if not titles:
        return "추천 조건에 맞는 프로그램을 비교해 아이에게 맞는 선택을 도와드릴게요."

    return f"{', '.join(titles)}를 아이 조건과 보호자 선호 기준으로 비교했어요."
