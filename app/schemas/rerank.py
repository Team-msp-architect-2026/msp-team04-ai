from pydantic import BaseModel, Field


class RerankCandidate(BaseModel):
    candidate_id: int = Field(alias="candidateId")
    title: str
    description: str | None = Field(default="")
    review_summary: str | None = Field(default="", alias="reviewSummary")
    semantic_score: float = Field(default=0.0, alias="semanticScore")

    model_config = {
        "populate_by_name": True,
    }


class RerankRequest(BaseModel):
    query: str = Field(min_length=1)
    candidates: list[RerankCandidate] = Field(default_factory=list, max_length=20)


class RerankResult(BaseModel):
    candidate_id: int = Field(alias="candidateId")
    rerank_score: float = Field(alias="rerankScore")

    model_config = {
        "populate_by_name": True,
    }


class RerankResponse(BaseModel):
    results: list[RerankResult]
    source: str
