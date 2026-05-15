from fastapi import APIRouter, HTTPException

from app.schemas.rerank import RerankRequest, RerankResponse
from app.services.rerank_service import rerank_candidates

router = APIRouter(prefix="/internal/ai", tags=["AI Reranker"])


@router.post("/rerank", response_model=RerankResponse)
async def rerank(
    request: RerankRequest,
) -> RerankResponse:
    try:
        return rerank_candidates(request)
    except Exception as error:
        raise HTTPException(
            status_code=502,
            detail=f"Rerank failed: {error}",
        ) from error
