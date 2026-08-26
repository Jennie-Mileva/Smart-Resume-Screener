from fastapi import FastAPI

from backend.app.api.resume import router as resume_router
from backend.app.api.candidates import router as candidates_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Smart Resume Screener",
    description="AI-powered resume screening and job matching system",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5505",
        "http://localhost:5505",
    ],
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