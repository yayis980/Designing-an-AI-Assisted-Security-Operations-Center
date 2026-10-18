from fastapi import FastAPI 
from app.database.connection import Base, engine
from app.database import models 

app = FastAPI(

    title = "AI-Asisted Security Operations Ceneter API",
    description=(
        "Backend API for security event ingestion, "
        "processing, and analysis."
    ),
    version="1.0.0",
)

@app.get("/api/v1/health", tags =["Health"])
def health_check():
    return {
        "status": "healthy", 
        "service": "soc-backend",
    }

Base.metadata.create_all(bind=engine)