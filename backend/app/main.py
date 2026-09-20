from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.started_at = datetime.now(timezone.utc)
    print(f"{settings.app_name} started.")
    yield
    print(f"{settings.app_name} stopped.")


app = FastAPI(
    title=settings.app_name,
    description="Real-time AI-powered media monitoring and crisis intelligence API.",
    version="0.1.0",
    debug=settings.debug,
    lifespan=lifespan,
)

cors_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    *(
        origin.strip()
        for origin in settings.cors_origins.split(",")
        if origin.strip()
    ),
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(
    api_router,
    prefix="/api/v1",
)


@app.get("/", tags=["System"])
async def root() -> dict:
    return {
        "application": settings.app_name,
        "version": "0.1.0",
        "status": "running",
        "docs": "/docs",
        "health": "/api/v1/health",
    }
