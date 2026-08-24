from pathlib import Path

from backend.app.services.pdf_extractor import extract_text_from_pdf
from backend.app.services.resume_parser import parse_resume
from backend.app.services.jd_parser import parse_job_description
from backend.app.services.matcher import match_resume_to_job


# Change this to your actual resume PDF path.
RESUME_PATH = Path("D:/RESUMECV_NEW.pdf")

# Put the JD you created here.
JOB_DESCRIPTION = """
PYTHON BACKEND DEVELOPER

About the Role
We are looking for a Python Backend Developer to join our engineering team.

Responsibilities
- Develop and maintain backend services using Python.
- Design and build RESTful APIs using FastAPI.
- Work with PostgreSQL databases and write efficient SQL queries.

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
- 1–2 years of experience in backend development or software engineering.
- Experience building and consuming REST APIs.
"""


def main():
    print("===== REAL RESUME MATCH TEST =====")

    if not RESUME_PATH.exists():
        print(f"\nERROR: Resume PDF not found:")
        print(RESUME_PATH.resolve())
        print("\nChange RESUME_PATH in this file to your actual PDF.")
        return

    # 1. Extract PDF text
    resume_text = extract_text_from_pdf(str(RESUME_PATH))

    if not resume_text:
        print("\nERROR: Could not extract text from resume PDF.")
        return

    print("\nPDF TEXT EXTRACTED:")
    print(f"{len(resume_text)} characters")

    # 2. Parse resume
    resume = parse_resume(resume_text)

    # 3. Parse JD
    jd = parse_job_description(JOB_DESCRIPTION)

    # 4. Match resume against JD
    result = match_resume_to_job(resume, jd)

    print("\n===== RESUME =====")
    print("Name:", resume.name)
    print("Skills:", ", ".join(resume.skills))

    print("\n===== JOB DESCRIPTION =====")
    print("Title:", jd.title)
    print("Required:", ", ".join(jd.required_skills))
    print("Preferred:", ", ".join(jd.preferred_skills))

    print("\n===== MATCH RESULT =====")

    # Pydantic model
    if hasattr(result, "model_dump"):
        result_data = result.model_dump()
    else:
        result_data = result

    for key, value in result_data.items():
        print(f"\n{key.upper()}:")
        print(value)

    print("\n===== END =====")


if __name__ == "__main__":
    main()