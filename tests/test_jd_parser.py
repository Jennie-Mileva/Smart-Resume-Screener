from backend.app.services.jd_parser import parse_job_description


def test_parse_job_description():
    jd_text = """
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

    jd = parse_job_description(jd_text)

    # Title
    assert jd.title == "PYTHON BACKEND DEVELOPER"

    # Required skills
    assert "Python" in jd.required_skills
    assert "FastAPI" in jd.required_skills
    assert "PostgreSQL" in jd.required_skills
    assert "Docker" in jd.required_skills

    # Preferred skills
    assert "AWS" in jd.preferred_skills
    assert "Redis" in jd.preferred_skills
    assert "Kubernetes" in jd.preferred_skills

    # Education
    assert len(jd.education_requirements) == 1

    # Experience
    assert len(jd.experience_requirements) == 2

    # Responsibilities
    assert len(jd.responsibilities) == 3