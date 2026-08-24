from fastapi import APIRouter, UploadFile, File, HTTPException
from pathlib import Path
import tempfile

from backend.app.services.pdf_extractor import extract_text_from_pdf


router = APIRouter(
    prefix="/api/resume",
    tags=["Resume"]
)

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB


@router.post("/upload")
async def upload_resume(file: UploadFile = File(...)):
    # 1. Check that a file was actually selected
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="No file was provided"
        )

    # 2. Check that the file is a PDF
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported"
        )

    # 3. Read the uploaded file
    file_contents = await file.read()

    # 4. Check file size
    if len(file_contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail="File size must not exceed 5 MB"
        )

    # 5. Check that the file isn't empty
    if len(file_contents) == 0:
        raise HTTPException(
            status_code=400,
            detail="The uploaded file is empty"
        )

    # 6. Save temporarily so pypdf can process it
    with tempfile.NamedTemporaryFile(
        suffix=".pdf",
        delete=False
    ) as temp_file:
        temp_file.write(file_contents)
        temp_file_path = Path(temp_file.name)

    try:
        # 7. Extract text from the PDF
        extracted_text = extract_text_from_pdf(
            str(temp_file_path)
        )

        # 8. Make sure the PDF actually contained text
        if not extracted_text:
            raise HTTPException(
                status_code=400,
                detail="Could not extract readable text from the PDF"
            )

        # 9. Return the extracted information
        return {
            "filename": file.filename,
            "text": extracted_text
        }

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Failed to process the PDF"
        ) from exc

    finally:
        # 10. Always delete the temporary file
        temp_file_path.unlink(missing_ok=True)