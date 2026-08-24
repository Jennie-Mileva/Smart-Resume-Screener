from pathlib import Path

from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_match_resume_api():
    jd_text = """
PYTHON BACKEND DEVELOPER

Responsibilities
- Develop and maintain backend services using Python.
- Design and build RESTful APIs using FastAPI.
- Work with PostgreSQL databases and write efficient SQL queries.
- Build containerized applications using Docker.

Required Skills
- Python
- FastAPI
- REST APIs
- PostgreSQL
- SQL
- Docker
- Git
- Object-Oriented Programming
- Data Structures and Algorithms

Preferred Skills
- AWS
- Redis
- Kubernetes
- React
- Machine Learning

Education
- Bachelor's degree in Computer Science, Information Technology, or a related field.

Experience
- 1-2 years of experience in backend development or software engineering.
- Experience building and consuming REST APIs.
- Experience working with relational databases.
"""

    resume_path = Path(r"D:\RESUMECV_NEW.pdf")

    assert resume_path.exists()

    with resume_path.open("rb") as resume_file:
        files = {
            "resume_file": (
                "resume.pdf",
                resume_file,
                "application/pdf",
            ),
            "job_description_file": (
                "job_description.txt",
                jd_text.encode("utf-8"),
                "text/plain",
            ),
        }

        response = client.post(
            "/api/resume/match",
            files=files,
        )

    assert response.status_code == 200

    result = response.json()

    assert result["candidate_name"] == "JENNIE MILEVA"
    assert "skill_match" in result
    assert "experience_match" in result
    assert "education_match" in result
    assert "project_match" in result
    assert "overall_score" in result