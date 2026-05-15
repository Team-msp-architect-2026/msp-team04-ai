from fastapi import APIRouter

from app.schemas.search_suggestion import (
    SearchSuggestionRequest,
    SearchSuggestionResponse,
)
from app.services.search_suggestion_service import generate_search_suggestions

router = APIRouter(prefix="/internal/ai", tags=["AI Search Suggestion"])


@router.post("/search-suggestions", response_model=SearchSuggestionResponse)
async def create_search_suggestions(
    request: SearchSuggestionRequest,
) -> SearchSuggestionResponse:
    return generate_search_suggestions(request)
