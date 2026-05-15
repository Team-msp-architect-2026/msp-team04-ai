import json
from app.schemas.search_suggestion import (
    SearchSuggestionRequest,
    SearchSuggestionResponse,
)
from app.services.openai_client import generate_search_suggestion_json


def generate_search_suggestions(
    request: SearchSuggestionRequest,
) -> SearchSuggestionResponse:
    try:
        prompt = build_prompt(request)
        result_json = generate_search_suggestion_json(prompt)
        suggestions = normalize_suggestions(result_json.get("suggestions", []))

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
                "name": child.name,
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
- 3~13세 자녀를 둔 부모가 검색창에서 바로 눌러볼 만한 한국어 검색어를 생성한다.
- 자녀 이름, 나이, 관심사, 최근 검색어, 공통 추천 키워드를 참고한다.
- 제공된 정보 밖의 프로그램명, 기관명, 혜택명은 지어내지 않는다.
- 검색어는 짧고 자연스러워야 한다.
- 부모가 실제로 검색할 만한 표현으로 만든다.
- 반드시 JSON만 반환한다.

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


def normalize_suggestions(raw_suggestions: list[object]) -> list[str]:
    suggestions: list[str] = []
    seen: set[str] = set()

    for item in raw_suggestions:
        if not isinstance(item, str):
            continue

        normalized = " ".join(item.split())

        if not normalized or normalized in seen:
            continue

        seen.add(normalized)
        suggestions.append(normalized)

    return suggestions


def generate_fallback_suggestions(
    request: SearchSuggestionRequest,
) -> SearchSuggestionResponse:
    suggestions: list[str] = []

    for child in request.children:
        child_name = child.name.strip()

        for concern in child.concerns:
            suggestions.append(f"{child_name}에게 맞는 {concern} 수업")

        if child.age is not None:
            suggestions.append(f"{child.age}세 아이를 위한 무료 공공 프로그램")

    for recent_search in request.recent_searches:
        if recent_search.strip():
            suggestions.append(recent_search.strip())

    for keyword in request.global_keywords:
        if keyword.strip():
            suggestions.append(keyword.strip())

    deduplicated: list[str] = []
    seen: set[str] = set()

    for suggestion in suggestions:
        normalized = " ".join(suggestion.split())

        if not normalized or normalized in seen:
            continue

        seen.add(normalized)
        deduplicated.append(normalized)

        if len(deduplicated) >= request.limit:
            break

    return SearchSuggestionResponse(
        suggestions=deduplicated,
        source="FALLBACK",
    )
