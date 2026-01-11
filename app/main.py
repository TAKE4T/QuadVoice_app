from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import generate, ingest
from app.core.config import settings

app = FastAPI(
    title="QuadVoice API",
    description="Adaptive content generation platform",
    version=settings.app_version,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ingest.router, prefix="/api/v1")
app.include_router(generate.router, prefix="/api/v1")


@app.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok", "app_version": settings.app_version}
