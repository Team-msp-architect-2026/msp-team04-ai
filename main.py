from fastapi import FastAPI

from app.routers.embedding import router as embedding_router
from app.routers.rerank import router as rerank_router
from app.routers.search_suggestion import router as search_suggestion_router
from app.routers.top3_compare import router as top3_compare_router

app = FastAPI(
    title="MoMent AI Service",
    description="MoMent OpenAI API based AI service",
    version="0.1.0",
)


@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "service": "moment-ai",
    }


app.include_router(search_suggestion_router)
app.include_router(embedding_router)
app.include_router(rerank_router)
app.include_router(top3_compare_router)
