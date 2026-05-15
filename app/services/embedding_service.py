from app.schemas.embedding import EmbeddingRequest, EmbeddingResponse
from app.services.openai_client import generate_embedding


def create_embedding(request: EmbeddingRequest) -> EmbeddingResponse:
    text = request.text.strip()

    if not text:
        raise ValueError("Embedding text must not be blank.")

    vector = generate_embedding(text)

    return EmbeddingResponse(
        source_id=request.source_id,
        source_type=request.source_type,
        vector=vector,
        success=True,
    )
