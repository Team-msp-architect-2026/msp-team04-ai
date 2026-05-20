from fastapi import APIRouter, HTTPException

from app.schemas.top3_compare import Top3CompareRequest, Top3CompareResponse
from app.services.top3_compare_service import generate_top3_compare

router = APIRouter(prefix="/internal/ai", tags=["AI Top3 Compare"])


@router.post("/top3-compare", response_model=Top3CompareResponse)
async def compare_top3(
    request: Top3CompareRequest,
) -> Top3CompareResponse:
    try:
        return generate_top3_compare(request)
    except Exception as error:
        raise HTTPException(
            status_code=502,
            detail=f"Top3 compare failed: {error}",
        ) from error
