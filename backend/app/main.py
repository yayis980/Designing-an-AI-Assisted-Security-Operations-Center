from fastapi import FastAPI 

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