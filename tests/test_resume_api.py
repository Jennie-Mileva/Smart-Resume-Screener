from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_upload_valid_pdf():
    with open(r"D:\RESUMECV_NEW.pdf", "rb") as pdf_file:
        response = client.post(
            "/api/resume/upload",
            files={
                "file": (
                    "RESUMECV_NEW.pdf",
                    pdf_file,
                    "application/pdf"
                )
            }
        )

    assert response.status_code == 200

    data = response.json()

    assert data["filename"] == "RESUMECV_NEW.pdf"
    assert len(data["text"]) > 0


def test_upload_non_pdf():
    response = client.post(
        "/api/resume/upload",
        files={
            "file": (
                "resume.txt",
                b"This is not a PDF",
                "text/plain"
            )
        }
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Only PDF files are supported"


def test_upload_empty_file():
    response = client.post(
        "/api/resume/upload",
        files={
            "file": (
                "empty.pdf",
                b"",
                "application/pdf"
            )
        }
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "The uploaded file is empty"


def test_upload_file_too_large():
    large_file = b"x" * (5 * 1024 * 1024 + 1)

    response = client.post(
        "/api/resume/upload",
        files={
            "file": (
                "large.pdf",
                large_file,
                "application/pdf"
            )
        }
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "File size must not exceed 5 MB"