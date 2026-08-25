from pathlib import Path

from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_screen_multiple_resumes():
    jd_text = """
PYTHON BACKEND DEVELOPER

Responsibilities
- Develop backend services using Python.
- Build REST APIs using FastAPI.
- Work with SQL databases.

Required Skills
- Python
- FastAPI
- SQL
- Git

Preferred Skills
- Docker
- AWS
"""

    resume_path = Path(r"D:\RESUMECV_NEW.pdf")

    assert resume_path.exists()

    with resume_path.open("rb") as resume_file:
        files = [
            (
                "resume_files",
                (
                    "resume1.pdf",
                    resume_file,
                    "application/pdf",
                ),
            ),
            (
                "resume_files",
                (
                    "resume2.pdf",
                    resume_file,
                    "application/pdf",
                ),
            ),
            (
                "job_description_file",
                (
                    "job_description.txt",
                    jd_text.encode("utf-8"),
                    "text/plain",
                ),
            ),
        ]

        response = client.post(
            "/api/resume/screen",
            files=files,
        )

    assert response.status_code == 200

    data = response.json()

    assert "job_title" in data
    assert "candidate_count" in data
    assert "candidates" in data

    assert data["candidate_count"] == 2
    assert len(data["candidates"]) == 2

    scores = [
        candidate["score"]
        for candidate in data["candidates"]
    ]

    assert scores == sorted(scores, reverse=True)