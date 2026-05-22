from fastapi import APIRouter, HTTPException

from app.schemas.next_recommend import NextRecommendRequest, NextRecommendResponse
from app.services.next_recommend_service import generate_next_recommend

router = APIRouter(prefix="/internal/ai", tags=["AI Next Recommend"])


@router.post("/next-recommend", response_model=NextRecommendResponse)
async def create_next_recommend(
    request: NextRecommendRequest,
) -> NextRecommendResponse:
    try:
        return generate_next_recommend(request)
    except Exception as error:
        raise HTTPException(
            status_code=502,
            detail=f"Next recommend failed: {error}",
        ) from error
