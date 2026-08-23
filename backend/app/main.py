from fastapi import FastAPI
app=FastAPI(
    title="Smart Resume Screener",
    description="AI-powered resume screening and job matching system",
    version="1.0.0"
)

@app.get("/api/health")
def health_check():
    return{
        "status" :"healthy",
        "service":"smart-resume-screener"
    }