from fastapi import FastAPI

from backend.app.api.resume import router as resume_router

app=FastAPI(
    title="Smart Resume Screener",
    description="AI-powered resume screening and job matching system",
    version="1.0.0"
)

app.include_router(resume_router)

@app.get("/api/health")
def health_check():
    return{
        "status" :"healthy",
        "service":"smart-resume-screener"
    }