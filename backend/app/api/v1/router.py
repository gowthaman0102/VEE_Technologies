from fastapi import APIRouter

from app.api.v1.articles import router as articles_router
from app.api.v1.clients import router as clients_router
from app.api.v1.companies import router as companies_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.embeddings import router as embeddings_router
from app.api.v1.health import router as health_router
from app.api.v1.ingestion import router as ingestion_router
from app.api.v1.processing import router as processing_router
from app.api.v1.risk import router as risk_router
from app.api.v1.semantic_search import router as semantic_search_router
from app.api.v1.triage import router as triage_router


api_router = APIRouter()

api_router.include_router(
    health_router,
    prefix="/health",
    tags=["Health"],
)

api_router.include_router(
    clients_router
)

api_router.include_router(
    companies_router
)

api_router.include_router(
    dashboard_router
)

api_router.include_router(
    articles_router
)

api_router.include_router(
    ingestion_router
)

api_router.include_router(
    processing_router
)

api_router.include_router(
    embeddings_router
)

api_router.include_router(
    semantic_search_router
)

api_router.include_router(
    triage_router
)

api_router.include_router(
    risk_router
)
