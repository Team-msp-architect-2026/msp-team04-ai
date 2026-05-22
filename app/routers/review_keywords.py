from fastapi import APIRouter, HTTPException

from app.schemas.review_keywords import ReviewKeywordsRequest, ReviewKeywordsResponse
from app.services.review_keywords_service import generate_review_keywords

router = APIRouter(prefix="/internal/ai", tags=["AI Review Keywords"])


@router.post("/review-keywords", response_model=ReviewKeywordsResponse)
async def create_review_keywords(
    request: ReviewKeywordsRequest,
) -> ReviewKeywordsResponse:
    try:
        return generate_review_keywords(request)
    except Exception as error:
        raise HTTPException(
            status_code=502,
            detail=f"Review keywords failed: {error}",
        ) from error
