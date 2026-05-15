from fastapi import APIRouter, HTTPException

from app.schemas.embedding import EmbeddingRequest, EmbeddingResponse
from app.services.embedding_service import create_embedding

router = APIRouter(prefix="/internal/ai", tags=["AI Embedding"])


@router.post("/embeddings", response_model=EmbeddingResponse)
async def create_text_embedding(
    request: EmbeddingRequest,
) -> EmbeddingResponse:
    try:
        return create_embedding(request)
    except Exception as error:
        raise HTTPException(
            status_code=502,
            detail=f"Embedding generation failed: {error}",
        ) from error
