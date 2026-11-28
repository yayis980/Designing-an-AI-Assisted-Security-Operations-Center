from fastapi import FastAPI

from app.database.connection import Base, engine
from app.database import models
from app.api.routes.alerts import router as alerts_router
from app.api.routes.events import router as events_router
from app.api.routes.servers import router as servers_router
from app.api.routes.scans import router as scans_router

app = FastAPI(
    title="AI-Assisted Security Operations Center API",
    description=(
        "Backend API for security event ingestion, "
        "processing, and analysis."
    ),
    version="1.0.0",
)

Base.metadata.create_all(bind=engine)

app.include_router(
    alerts_router,
    prefix="/api/v1/alerts",
)

app.include_router(
    events_router,
    prefix="/api/v1/events",
)


app.include_router(
    servers_router,
    prefix="/api/v1/servers",
)

app.include_router(
    scans_router,
    prefix="/api/v1/scans",
)


@app.get("/", tags=["Home"])
def root():
    return {
        "message": "Welcome to the AI-Assisted Security Operations Center API",
        "docs": "/docs",
        "status": "online",
    }


@app.get("/api/v1/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "service": "soc-backend",
    }
