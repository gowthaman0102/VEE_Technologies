from fastapi import APIRouter

from app.api.v1.clients import router as clients_router
from app.api.v1.companies import router as companies_router
from app.api.v1.health import router as health_router


api_router = APIRouter()

api_router.include_router(
    health_router,
    prefix="/health",
    tags=["Health"],
)

api_router.include_router(clients_router)

api_router.include_router(companies_router)
