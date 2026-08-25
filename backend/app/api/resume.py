from pathlib import Path
import tempfile

from fastapi import (
    APIRouter,
    UploadFile,
    File,
    HTTPException,
    Depends,
)

from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.services.database_service import (
    create_candidate,
    create_resume_profile,
    get_all_candidates,
)
from backend.app.services.pdf_extractor import extract_text_from_pdf
from backend.app.services.resume_parser import parse_resume
from backend.app.services.jd_parser import parse_job_description
from backend.app.services.matcher import match_resume_to_job
from backend.app.services.llm_matcher import (
    llm_match_resume_to_job,
)
from backend.app.services.screener import screen_candidates


router = APIRouter(
    prefix="/api/resume",
    tags=["Resume"],
)

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB


@router.post("/upload")
async def upload_resume(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Upload a resume PDF, extract and parse its text,
    then save the candidate and resume profile to SQLite.
    """

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="No file was provided",
        )

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported",
        )

    file_contents = await file.read()

    if len(file_contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail="File size must not exceed 5 MB",
        )

    if len(file_contents) == 0:
        raise HTTPException(
            status_code=400,
            detail="The uploaded file is empty",
        )

    with tempfile.NamedTemporaryFile(
        suffix=".pdf",
        delete=False,
    ) as temp_file:
        temp_file.write(file_contents)
        temp_file_path = Path(temp_file.name)

    try:
        extracted_text = extract_text_from_pdf(
            str(temp_file_path)
        )

        if not extracted_text:
            raise HTTPException(
                status_code=400,
                detail="Could not extract readable text from the PDF",
            )

        parsed_resume = parse_resume(
            extracted_text
        )

        candidate = create_candidate(
            db=db,
            name=parsed_resume.name,
            email=getattr(
                parsed_resume,
                "email",
                None,
            ),
            resume_filename=file.filename,
            raw_text=extracted_text,
        )

        create_resume_profile(
            db=db,
            candidate_id=candidate.id,
            skills=parsed_resume.skills,
            education=[
                item.model_dump()
                for item in parsed_resume.education
            ],
            experience=[
                item.model_dump()
                for item in parsed_resume.experience
            ],
        )

        return {
            "id": candidate.id,
            "filename": candidate.resume_filename,
            "name": candidate.name,
            "email": candidate.email,
            "text": candidate.raw_text,
        }

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Failed to process the PDF",
        ) from exc

    finally:
        temp_file_path.unlink(
            missing_ok=True
        )


@router.get("/resumes")
def get_resumes(
    db: Session = Depends(get_db),
):
    """
    Return all candidates stored in the database.
    """

    candidates = get_all_candidates(db)

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


@router.post("/match")
async def match_resume(
    resume_file: UploadFile = File(...),
    job_description_file: UploadFile = File(...),
):
    """
    Match a single resume PDF against one job description.
    """

    if not resume_file.filename:
        raise HTTPException(
            status_code=400,
            detail="No resume file was provided",
        )

    if not resume_file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Resume must be a PDF file",
        )

    if not job_description_file.filename:
        raise HTTPException(
            status_code=400,
            detail="No job description file was provided",
        )

    if not job_description_file.filename.lower().endswith(".txt"):
        raise HTTPException(
            status_code=400,
            detail="Job description must be a .txt file",
        )

    resume_contents = await resume_file.read()

    if len(resume_contents) == 0:
        raise HTTPException(
            status_code=400,
            detail="The uploaded resume is empty",
        )

    if len(resume_contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail="Resume file size must not exceed 5 MB",
        )

    jd_contents = await job_description_file.read()

    if len(jd_contents) == 0:
        raise HTTPException(
            status_code=400,
            detail="The job description file is empty",
        )

    if len(jd_contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail="Job description file size must not exceed 5 MB",
        )

    try:
        job_description_text = jd_contents.decode(
            "utf-8"
        ).strip()

    except UnicodeDecodeError as exc:
        raise HTTPException(
            status_code=400,
            detail="Job description must be a UTF-8 text file",
        ) from exc

    if not job_description_text:
        raise HTTPException(
            status_code=400,
            detail="Job description cannot be empty",
        )

    with tempfile.NamedTemporaryFile(
        suffix=".pdf",
        delete=False,
    ) as temp_file:
        temp_file.write(resume_contents)
        temp_file_path = Path(temp_file.name)

    try:
        resume_text = extract_text_from_pdf(
            str(temp_file_path)
        )

        if not resume_text:
            raise HTTPException(
                status_code=400,
                detail="Could not extract readable text from the PDF",
            )

        resume = parse_resume(
            resume_text
        )

        jd = parse_job_description(
            job_description_text
        )

        result = match_resume_to_job(
            resume,
            jd,
        )

        response = result.model_dump()

        try:
            llm_result = llm_match_resume_to_job(
                resume,
                jd,
            )

            response["llm_match"] = llm_result

        except Exception as exc:
            print(
                "\n===== LLM MATCH FALLBACK ====="
            )
            print(
                f"{type(exc).__name__}: {exc}"
            )
            print(
                "Using deterministic matcher result."
            )
            print(
                "==============================\n"
            )

            response["llm_match"] = {
                "available": False,
                "fallback": True,
                "reason": "LLM service unavailable",
            }

        return response

    except HTTPException:
        raise

    except Exception as exc:
        print("\n===== LLM/API ERROR =====")
        print(type(exc).__name__)
        print(str(exc))
        print("=========================\n")

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc

    finally:
        temp_file_path.unlink(
            missing_ok=True
        )


@router.post("/screen")
async def screen_resumes(
    resume_files: list[UploadFile] = File(...),
    job_description_file: UploadFile = File(...),
):
    """
    Screen multiple resume PDFs against one job description.

    Candidates are parsed, matched using the LLM,
    classified, and sorted by score.
    """

    if not resume_files:
        raise HTTPException(
            status_code=400,
            detail="At least one resume is required",
        )

    if not job_description_file.filename:
        raise HTTPException(
            status_code=400,
            detail="No job description file was provided",
        )

    if not job_description_file.filename.lower().endswith(".txt"):
        raise HTTPException(
            status_code=400,
            detail="Job description must be a .txt file",
        )

    jd_contents = await job_description_file.read()

    if not jd_contents:
        raise HTTPException(
            status_code=400,
            detail="The job description file is empty",
        )

    if len(jd_contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail="Job description file size must not exceed 5 MB",
        )

    try:
        job_description_text = jd_contents.decode(
            "utf-8"
        ).strip()

    except UnicodeDecodeError as exc:
        raise HTTPException(
            status_code=400,
            detail="Job description must be a UTF-8 text file",
        ) from exc

    if not job_description_text:
        raise HTTPException(
            status_code=400,
            detail="Job description cannot be empty",
        )

    jd = parse_job_description(
        job_description_text
    )

    resumes = []

    for resume_file in resume_files:

        if not resume_file.filename:
            continue

        if not resume_file.filename.lower().endswith(".pdf"):
            raise HTTPException(
                status_code=400,
                detail=f"{resume_file.filename} is not a PDF file",
            )

        contents = await resume_file.read()

        if not contents:
            continue

        if len(contents) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"{resume_file.filename} exceeds the 5 MB limit",
            )

        with tempfile.NamedTemporaryFile(
            suffix=".pdf",
            delete=False,
        ) as temp_file:
            temp_file.write(contents)
            temp_path = Path(temp_file.name)

        try:
            resume_text = extract_text_from_pdf(
                str(temp_path)
            )

            if not resume_text:
                continue

            resume = parse_resume(
                resume_text
            )

            resumes.append(
                {
                    "filename": resume_file.filename,
                    "resume": resume,
                }
            )

        finally:
            temp_path.unlink(
                missing_ok=True
            )

    if not resumes:
        raise HTTPException(
            status_code=400,
            detail="No valid resumes were provided",
        )

    results = screen_candidates(
        resumes,
        jd,
    )

    return {
        "job_title": jd.title,
        "candidate_count": len(results),
        "candidates": results,
    }