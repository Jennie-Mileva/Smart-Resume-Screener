from pathlib import Path
import tempfile

from fastapi import (
    APIRouter,
    UploadFile,
    File,
    HTTPException,
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
):
    """Upload a resume PDF and extract its text."""

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

        return {
            "filename": file.filename,
            "text": extracted_text,
        }

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Failed to process the PDF",
        ) from exc

    finally:
        temp_file_path.unlink(missing_ok=True)


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

        resume = parse_resume(resume_text)

        jd = parse_job_description(
            job_description_text
        )

        result = match_resume_to_job(
            resume,
            jd,
        )

        llm_result = llm_match_resume_to_job(
            resume,
            jd,
        )

        response = result.model_dump()
        response["llm_match"] = llm_result

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

    # --------------------------------------------------
    # 1. Validate resumes
    # --------------------------------------------------

    if not resume_files:
        raise HTTPException(
            status_code=400,
            detail="At least one resume is required",
        )

    # --------------------------------------------------
    # 2. Validate JD
    # --------------------------------------------------

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

    # --------------------------------------------------
    # 3. Parse JD
    # --------------------------------------------------

    jd = parse_job_description(
        job_description_text
    )

    # --------------------------------------------------
    # 4. Process all resumes
    # --------------------------------------------------

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

            # Keep filename available for screening results
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

    # --------------------------------------------------
    # 5. Validate candidates
    # --------------------------------------------------

    if not resumes:
        raise HTTPException(
            status_code=400,
            detail="No valid resumes were provided",
        )

    # --------------------------------------------------
    # 6. Screen candidates
    # --------------------------------------------------

    results = screen_candidates(
        resumes,
        jd,
    )

    # --------------------------------------------------
    # 7. Return ranked results
    # --------------------------------------------------

    return {
        "job_title": jd.title,
        "candidate_count": len(results),
        "candidates": results,
    }