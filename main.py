import time

from fastapi import FastAPI, Request, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

from app.routers.embedding import router as embedding_router
from app.routers.rerank import router as rerank_router
from app.routers.search_suggestion import router as search_suggestion_router
from app.routers.top3_compare import router as top3_compare_router
from app.routers.program_reason import router as program_reason_router
from app.routers.review_keywords import router as review_keywords_router
from app.routers.parenting_report import router as parenting_report_router
from app.routers.next_recommend import router as next_recommend_router


app = FastAPI(
    title="MoMent AI Service",
    description="MoMent OpenAI API based AI service",
    version="0.1.0",
)


REQUEST_COUNT = Counter(
    "moment_ai_http_requests_total",
    "Total HTTP requests handled by MoMent AI Service",
    ["method", "path", "status"],
)

REQUEST_LATENCY = Histogram(
    "moment_ai_http_request_duration_seconds",
    "HTTP request latency for MoMent AI Service",
    ["method", "path"],
)


def get_route_template(request: Request) -> str:
    route = request.scope.get("route")
    path = getattr(route, "path", None)

    if path:
        return path

    return request.url.path


@app.middleware("http")
async def prometheus_metrics_middleware(request: Request, call_next):
    start_time = time.monotonic()
    response = None

    try:
        response = await call_next(request)
        return response
    finally:
        path = get_route_template(request)

        if path != "/metrics":
            duration = time.monotonic() - start_time
            status_code = str(response.status_code) if response is not None else "500"

            REQUEST_COUNT.labels(
                method=request.method,
                path=path,
                status=status_code,
            ).inc()

            REQUEST_LATENCY.labels(
                method=request.method,
                path=path,
            ).observe(duration)


@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "service": "moment-ai",
    }


@app.get("/metrics")
async def metrics():
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )


app.include_router(search_suggestion_router)
app.include_router(embedding_router)
app.include_router(rerank_router)
app.include_router(top3_compare_router)
app.include_router(program_reason_router)
app.include_router(review_keywords_router)
app.include_router(parenting_report_router)
app.include_router(next_recommend_router)
