from backend.app.database import Base, SessionLocal, engine
from backend.app.services.database_service import (
    create_candidate,
    create_resume_profile,
    create_job,
    create_screening_result,
)


def test_database_service():
    Base.metadata.create_all(engine)

    db = SessionLocal()

    try:
        candidate = create_candidate(
            db=db,
            name="Test Candidate",
            email="test@example.com",
            resume_filename="test.pdf",
            raw_text="Python FastAPI SQL",
        )

        assert candidate.id is not None

        profile = create_resume_profile(
            db=db,
            candidate_id=candidate.id,
            skills=["Python", "FastAPI"],
            education=["Bachelor's"],
            experience=["Backend Developer"],
        )

        assert profile.id is not None

        job = create_job(
            db=db,
            title="Python Backend Developer",
            description="Python FastAPI SQL",
        )

        assert job.id is not None

        result = create_screening_result(
            db=db,
            candidate_id=candidate.id,
            job_id=job.id,
            score=8.7,
            recommendation="Strong Match",
            matched_skills=["Python", "FastAPI"],
            missing_skills=["AWS"],
            justification="Strong backend experience.",
        )

        assert result.id is not None
        assert result.score == 8.7

    finally:
        db.close()