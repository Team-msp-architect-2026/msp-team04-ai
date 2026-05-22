from fastapi import APIRouter, HTTPException

from app.schemas.parenting_report import ParentingReportRequest, ParentingReportResponse
from app.services.parenting_report_service import generate_parenting_report

router = APIRouter(prefix="/internal/ai", tags=["AI Parenting Report"])


@router.post("/parenting-report", response_model=ParentingReportResponse)
async def create_parenting_report(
    request: ParentingReportRequest,
) -> ParentingReportResponse:
    try:
        return generate_parenting_report(request)
    except Exception as error:
        raise HTTPException(
            status_code=502,
            detail=f"Parenting report failed: {error}",
        ) from error
