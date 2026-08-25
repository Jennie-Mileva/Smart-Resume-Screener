from sqlalchemy.orm import Session

from backend.app.models.candidate import Candidate
from backend.app.models.resume_profile import ResumeProfile
from backend.app.models.job import Job
from backend.app.models.screening_result import ScreeningResult


def create_candidate(
    db: Session,
    name: str | None,
    email: str | None,
    resume_filename: str,
    raw_text: str,
) -> Candidate:

    candidate = Candidate(
        name=name,
        email=email,
        resume_filename=resume_filename,
        raw_text=raw_text,
    )

    db.add(candidate)
    db.commit()
    db.refresh(candidate)

    return candidate


def create_resume_profile(
    db: Session,
    candidate_id: int,
    skills: list,
    education: list,
    experience: list,
) -> ResumeProfile:

    profile = ResumeProfile(
        candidate_id=candidate_id,
        skills=skills,
        education=education,
        experience=experience,
    )

    db.add(profile)
    db.commit()
    db.refresh(profile)

    return profile


def create_job(
    db: Session,
    title: str,
    description: str,
) -> Job:

    job = Job(
        title=title,
        description=description,
    )

    db.add(job)
    db.commit()
    db.refresh(job)

    return job


def create_screening_result(
    db: Session,
    candidate_id: int,
    job_id: int,
    score: float,
    recommendation: str,
    matched_skills: list,
    missing_skills: list,
    justification: str,
) -> ScreeningResult:

    result = ScreeningResult(
        candidate_id=candidate_id,
        job_id=job_id,
        score=score,
        recommendation=recommendation,
        matched_skills=matched_skills,
        missing_skills=missing_skills,
        justification=justification,
    )

    db.add(result)
    db.commit()
    db.refresh(result)

    return result
def get_all_candidates(
    db: Session,
) -> list[Candidate]:
        return (
            db.query(Candidate)
            .order_by(Candidate.created_at.desc())
            .all()
        )