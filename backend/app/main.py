import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.resume import router as resume_router
from backend.app.api.candidates import router as candidates_router


app = FastAPI(
    title="Smart Resume Screener",
    description="AI-powered resume screening and job matching system",
    version="1.0.0",
)


frontend_url = os.getenv(
    "FRONTEND_URL",
    "http://127.0.0.1:5505",
)

allowed_origins = [
    "http://127.0.0.1:5505",
    "http://localhost:5505",
]

if frontend_url not in allowed_origins:
    allowed_origins.append(frontend_url)


app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(resume_router)
app.include_router(candidates_router)


@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": "smart-resume-screener",
    }