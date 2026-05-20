from fastapi import APIRouter, HTTPException

from app.schemas.program_reason import ProgramReasonRequest, ProgramReasonResponse
from app.services.program_reason_service import generate_program_reason

router = APIRouter(prefix="/internal/ai", tags=["AI Program Reason"])


@router.post("/program-reason", response_model=ProgramReasonResponse)
async def create_program_reason(
    request: ProgramReasonRequest,
) -> ProgramReasonResponse:
    try:
        return generate_program_reason(request)
    except Exception as error:
        raise HTTPException(
            status_code=502,
            detail=f"Program reason failed: {error}",
        ) from error
