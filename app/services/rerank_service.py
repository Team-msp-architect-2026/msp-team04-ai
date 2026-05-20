import json
from typing import Any

from app.schemas.rerank import (
    RerankCandidate,
    RerankRequest,
    RerankResponse,
    RerankResult,
)
from app.services.openai_client import generate_rerank_json


def rerank_candidates(request: RerankRequest) -> RerankResponse:
    if not request.candidates:
        return RerankResponse(results=[], source="OPENAI")

    prompt = build_prompt(request)
    result_json = generate_rerank_json(prompt)
    results = normalize_results(result_json, request.candidates)

    return RerankResponse(
        results=results,
        source="OPENAI",
    )


def build_prompt(request: RerankRequest) -> str:
    payload = {
        "query": request.query,
        "candidates": [
            {
                "candidateId": candidate.candidate_id,
                "title": candidate.title,
                "description": candidate.description or "",
                "reviewSummary": candidate.review_summary or "",
                "semanticScore": candidate.semantic_score,
            }
            for candidate in request.candidates
        ],
    }

    return f"""
너는 MoMent 교육/돌봄 프로그램 검색 결과 Reranker다.

목표:
- 사용자의 검색어(query)에 가장 잘 맞는 프로그램 후보를 재정렬하기 위한 rerankScore를 계산한다.
- 후보는 OpenSearch Vector Search에서 먼저 가져온 최대 20개 프로그램이다.
- 너는 후보를 새로 만들거나 삭제하지 않는다.
- 반드시 입력으로 받은 candidateId만 사용한다.
- 가능한 모든 후보에 대해 rerankScore를 반환한다.
- rerankScore는 0.0 이상 1.0 이하 숫자다.
- query와 title, description, reviewSummary의 의미적 관련성을 가장 중요하게 본다.
- semanticScore는 1차 검색 점수 참고값으로만 사용한다.
- 실제로 제공되지 않은 프로그램 정보, 기관명, 혜택명은 절대 지어내지 않는다.
- 반드시 JSON만 반환한다.

점수 기준:
- 0.90~1.00: query 의도와 매우 직접적으로 일치
- 0.70~0.89: query 의도와 꽤 관련 있음
- 0.40~0.69: 일부 관련 있음
- 0.00~0.39: 관련성이 낮음

출력 JSON 형식:
{{
  "results": [
    {{
      "candidateId": 1,
      "rerankScore": 0.95
    }}
  ]
}}

입력 데이터:
{json.dumps(payload, ensure_ascii=False)}
""".strip()


def normalize_results(
    result_json: dict[str, Any],
    candidates: list[RerankCandidate],
) -> list[RerankResult]:
    raw_results = result_json.get("results")

    if not isinstance(raw_results, list):
        raise ValueError("Rerank response must contain results array.")

    candidate_map = {candidate.candidate_id: candidate for candidate in candidates}
    seen: set[int] = set()
    score_map: dict[int, float] = {}

    for item in raw_results:
        if not isinstance(item, dict):
            continue

        candidate_id = item.get("candidateId")
        rerank_score = item.get("rerankScore")

        if candidate_id is None or rerank_score is None:
            continue

        try:
            candidate_id = int(candidate_id)
            rerank_score = float(rerank_score)
        except (TypeError, ValueError):
            continue

        if candidate_id not in candidate_map:
            continue

        if candidate_id in seen:
            continue

        seen.add(candidate_id)
        score_map[candidate_id] = max(0.0, min(1.0, rerank_score))

    results: list[RerankResult] = []

    for candidate in candidates:
        score = score_map.get(candidate.candidate_id)

        if score is None:
            # OpenAI가 일부 후보를 누락한 경우 전체 요청을 실패시키지 않고
            # 기존 OpenSearch semanticScore를 보존해서 Backend가 전체 후보를 병합할 수 있게 한다.
            score = max(0.0, min(1.0, float(candidate.semantic_score or 0.0)))

        results.append(
            RerankResult(
                candidate_id=candidate.candidate_id,
                rerank_score=score,
            )
        )

    return results
