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
    Match a resume PDF against a job-description text file.

    resume_file:
        Resume PDF.

    job_description_file:
        Plain-text JD file (.txt).
    """

    # --------------------------------------------------
    # 1. Validate resume
    # --------------------------------------------------

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

    # --------------------------------------------------
    # 2. Validate JD file
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

    # --------------------------------------------------
    # 3. Read resume PDF
    # --------------------------------------------------

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

    # --------------------------------------------------
    # 4. Read JD text file
    # --------------------------------------------------

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

    # --------------------------------------------------
    # 5. Save resume temporarily
    # --------------------------------------------------

    with tempfile.NamedTemporaryFile(
        suffix=".pdf",
        delete=False,
    ) as temp_file:
        temp_file.write(resume_contents)
        temp_file_path = Path(temp_file.name)

    try:

        # --------------------------------------------------
        # 6. Extract resume text
        # --------------------------------------------------

        resume_text = extract_text_from_pdf(
            str(temp_file_path)
        )

        if not resume_text:
            raise HTTPException(
                status_code=400,
                detail="Could not extract readable text from the PDF",
            )

        # --------------------------------------------------
        # 7. Parse resume
        # --------------------------------------------------

        resume = parse_resume(
            resume_text
        )

        # --------------------------------------------------
        # 8. Parse job description
        # --------------------------------------------------

        jd = parse_job_description(
            job_description_text
        )
        print("\n===== JD TEXT RECEIVED =====")
        print(job_description_text)
        print("============================")

        print("\n===== JD OBJECT =====")
        print(jd)
        print("=====================")
        # --------------------------------------------------
        # 9. Match resume against JD
        # --------------------------------------------------

        result = match_resume_to_job(
            resume,
            jd,
        )

        # --------------------------------------------------
        # 10. Return result
        # --------------------------------------------------

        return result.model_dump()

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Failed to match resume against job description",
        ) from exc

    finally:
        temp_file_path.unlink(
            missing_ok=True
        )