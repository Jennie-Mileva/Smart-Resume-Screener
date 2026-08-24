from backend.app.schemas.job_description import JobDescription
from backend.app.schemas.resume import Resume
from backend.app.services.matcher import match_resume_to_job


def test_match_resume_to_job():
    resume = Resume(
        name="Jennie Mileva",
        email="jenniemileva10@gmail.com",
        phone="+91 9188292650",
        skills=[
            "Python",
            "Java",
            "React",
            "MongoDB",
            "AWS",
        ],
    )

    jd = JobDescription(
        title="Python Backend Developer",
        required_skills=[
            "Python",
            "FastAPI",
            "PostgreSQL",
            "Docker",
            "SQL",
        ],
        preferred_skills=[
            "AWS",
            "React",
            "Redis",
        ],
        education_requirements=[],
        experience_requirements=[],
        responsibilities=[],
    )

    result = match_resume_to_job(resume, jd)

    assert result.candidate_name == "Jennie Mileva"

    assert result.skill_match.matched_required_skills == [
        "Python"
    ]

    assert result.skill_match.missing_required_skills == [
        "FastAPI",
        "PostgreSQL",
        "Docker",
        "SQL",
    ]

    assert result.skill_match.required_match_percentage == 20.0

    assert result.skill_match.matched_preferred_skills == [
        "AWS",
        "React",
    ]

    assert result.skill_match.missing_preferred_skills == [
        "Redis"
    ]

    assert result.skill_match.preferred_match_percentage == 66.67

    assert result.overall_score == 29.33


def test_experience_matching():
    resume = Resume(
        name="Jennie Mileva",
        experience=[
            {
                "company": "ABC Technologies",
                "role": "Python Backend Developer",
                "start_date": "2024",
                "end_date": "2025",
                "description": (
                    "Developed Python backend services "
                    "and REST APIs."
                ),
            }
        ],
    )

    jd = JobDescription(
        title="Python Backend Developer",
        required_skills=[],
        preferred_skills=[],
        education_requirements=[],
        experience_requirements=[
            "1–2 years of experience in backend development",
            "Experience building and consuming REST APIs",
        ],
        responsibilities=[],
    )

    result = match_resume_to_job(resume, jd)

    assert result.experience_match.matched is True
    assert result.experience_match.match_percentage > 0


def test_project_matching():
    resume = Resume(
        name="Jennie Mileva",
        projects=[
            {
                "title": "Smart Resume Screener",
                "description": (
                    "Built a resume screening application "
                    "using Python and FastAPI."
                ),
                "technologies": [
                    "Python",
                    "FastAPI",
                    "PostgreSQL",
                ],
            },
            {
                "title": "E-Commerce Application",
                "description": (
                    "Built an e-commerce web application "
                    "using React and MongoDB."
                ),
                "technologies": [
                    "React",
                    "MongoDB",
                ],
            },
        ],
    )

    jd = JobDescription(
        title="Python Backend Developer",
        required_skills=[],
        preferred_skills=[],
        education_requirements=[],
        experience_requirements=[],
        responsibilities=[
            "Build backend services using Python and FastAPI.",
            "Develop REST APIs.",
        ],
    )

    result = match_resume_to_job(resume, jd)

    assert len(result.project_match.matched_projects) > 0
    assert result.project_match.match_percentage > 0