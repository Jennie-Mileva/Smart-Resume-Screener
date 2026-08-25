from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models.candidate import Candidate


router = APIRouter(
    prefix="/api/resumes",
    tags=["Resumes"],
)


@router.get("")
def get_resumes(
    db: Session = Depends(get_db),
):
    candidates = (
        db.query(Candidate)
        .order_by(Candidate.created_at.desc())
        .all()
    )

    return {
        "count": len(candidates),
        "candidates": [
            {
                "id": candidate.id,
                "name": candidate.name,
                "email": candidate.email,
                "resume_filename": candidate.resume_filename,
                "created_at": candidate.created_at,
            }
            for candidate in candidates
        ],
    }