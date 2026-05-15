import json
import re

from app.schemas.search_suggestion import (
    SearchSuggestionRequest,
    SearchSuggestionResponse,
)
from app.services.openai_client import generate_search_suggestion_json

FORBIDDEN_WORDS = [
    "자료",
    "문제집",
    "문제",
    "앱",
    "게임",
    "공부법",
    "팁",
]

MAX_SUGGESTION_LENGTH = 17


def generate_search_suggestions(
    request: SearchSuggestionRequest,
) -> SearchSuggestionResponse:
    try:
        prompt = build_prompt(request)
        result_json = generate_search_suggestion_json(prompt)
        suggestions = normalize_suggestions(
            raw_suggestions=result_json.get("suggestions", []),
            request=request,
        )

        suggestions = fill_missing_suggestions(
            suggestions=suggestions,
            request=request,
        )

        if suggestions:
            return SearchSuggestionResponse(
                suggestions=suggestions[: request.limit],
                source="OPENAI",
            )
    except Exception as error:
        print(f"[search-suggestions] OpenAI fallback. error={error}")

    return generate_fallback_suggestions(request)


def build_prompt(request: SearchSuggestionRequest) -> str:
    payload = {
        "children": [
            {
                "age": child.age,
                "concerns": child.concerns,
            }
            for child in request.children
        ],
        "recent_searches": request.recent_searches,
        "global_keywords": request.global_keywords,
        "limit": request.limit,
    }

    return f"""
너는 MoMent의 AI 추천 검색어 생성기다.

목표:
- 3~13세 자녀를 둔 부모가 MoMent 앱에서 교육/돌봄 프로그램을 찾기 위해 검색창에 입력할 만한 한국어 검색어를 생성한다.
- 자녀 나이, 관심사, 최근 검색어, 공통 추천 키워드를 참고한다.
- 추천 검색어에 자녀 이름은 절대 넣지 않는다.
- 반드시 교육 프로그램, 돌봄 프로그램, 공공 프로그램, 체험 프로그램을 찾는 검색어만 생성한다.
- 외부 학습자료, 문제집, 문제, 앱, 게임, 공부법, 팁 같은 일반 웹검색 표현은 절대 만들지 않는다.
- 제공된 정보 밖의 실제 프로그램명, 기관명, 혜택명은 지어내지 않는다.
- 검색어는 최대 5개만 생성한다.
- 각 검색어는 17자를 넘기지 않는다.
- 불필요한 띄어쓰기나 비정상적인 공백을 만들지 않는다.
- 검색창에 바로 넣기 좋은 간결한 표현으로 만든다.
- 반드시 JSON만 반환한다.

좋은 예시:
{{
  "suggestions": [
    "무료 미술 수업",
    "소규모 코딩 수업",
    "주말 돌봄 프로그램",
    "사회성 체험활동",
    "공공 체육 프로그램"
  ]
}}

나쁜 예시:
{{
  "suggestions": [
    "민준 수학 문제집",
    "코딩 앱 추천",
    "사회성 향상 게임",
    "기초학습 팁"
  ]
}}

출력 JSON 형식:
{{
  "suggestions": [
    "검색어1",
    "검색어2"
  ]
}}

입력 데이터:
{json.dumps(payload, ensure_ascii=False)}
""".strip()


def normalize_suggestions(
    raw_suggestions: list[object],
    request: SearchSuggestionRequest,
) -> list[str]:
    suggestions: list[str] = []
    seen: set[str] = set()
    child_names = {
        child.name.strip()
        for child in request.children
        if child.name and child.name.strip()
    }

    for item in raw_suggestions:
        if not isinstance(item, str):
            continue

        normalized = normalize_keyword(item)

        for child_name in child_names:
            normalized = normalized.replace(child_name, "").strip()

        normalized = normalize_keyword(normalized)

        if not is_valid_suggestion(normalized):
            continue

        if normalized in seen:
            continue

        seen.add(normalized)
        suggestions.append(normalized)

        if len(suggestions) >= request.limit:
            break

    return suggestions


def fill_missing_suggestions(
    suggestions: list[str],
    request: SearchSuggestionRequest,
) -> list[str]:
    candidates: list[str] = []

    for child in request.children:
        for concern in child.concerns:
            candidates.extend(build_concern_keywords(concern))

        if child.age is not None:
            candidates.append(f"{child.age}세 무료 수업")

    for keyword in request.global_keywords:
        candidates.append(keyword)

    for keyword in request.recent_searches:
        candidates.append(keyword)

    seen = set(suggestions)
    filled = list(suggestions)

    for candidate in candidates:
        normalized = normalize_keyword(candidate)

        if not is_valid_suggestion(normalized):
            continue

        if normalized in seen:
            continue

        seen.add(normalized)
        filled.append(normalized)

        if len(filled) >= request.limit:
            break

    return filled


def build_concern_keywords(concern: str) -> list[str]:
    concern = normalize_keyword(concern)

    mapping = {
        "학습": ["기초학습 수업", "소규모 학습반"],
        "기초학습": ["기초학습 수업", "소규모 학습반"],
        "수학": ["수학 기초반", "놀이 수학 수업"],
        "코딩": ["코딩 체험 수업", "초등 코딩 수업"],
        "미술": ["무료 미술 수업", "창의 미술 수업"],
        "창의력": ["창의력 체험활동", "창의 미술 수업"],
        "사회성": ["사회성 체험활동", "또래 활동 수업"],
        "친구 관계": ["사회성 체험활동", "또래 활동 수업"],
        "성격": ["정서지원 활동", "사회성 체험활동"],
        "진로": ["진로 체험활동", "직업 체험 수업"],
        "체육": ["공공 체육 수업", "주말 체육 활동"],
        "영어": ["영어 기초 수업", "영어 회화 수업"],
        "독서": ["독서 토론 수업", "책놀이 수업"],
    }

    return mapping.get(concern, [f"{concern} 맞춤 수업"])


def is_valid_suggestion(keyword: str) -> bool:
    if not keyword:
        return False

    if len(keyword) > MAX_SUGGESTION_LENGTH:
        return False

    return not any(forbidden in keyword for forbidden in FORBIDDEN_WORDS)


def normalize_keyword(keyword: str) -> str:
    normalized = keyword.replace("\u00a0", " ").replace("\u200b", "")
    normalized = re.sub(r"\\s+", " ", normalized).strip()

    replacements = {
        "프로 그램": "프로그램",
        "프 로그램": "프로그램",
        "미 술": "미술",
        "코 딩": "코딩",
        "수 업": "수업",
        "체 험": "체험",
        "돌 봄": "돌봄",
        "놀이  활동": "놀이 활동",
        "돌봄 서비스": "돌봄",
    }

    for source, target in replacements.items():
        normalized = normalized.replace(source, target)

    normalized = re.sub(r"\\s+", " ", normalized).strip()

    return normalized


def generate_fallback_suggestions(
    request: SearchSuggestionRequest,
) -> SearchSuggestionResponse:
    suggestions = fill_missing_suggestions(
        suggestions=[],
        request=request,
    )

    return SearchSuggestionResponse(
        suggestions=suggestions[: request.limit],
        source="FALLBACK",
    )
