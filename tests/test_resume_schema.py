from backend.app.schemas.resume import (
    Resume,
    Education,
    Project,
    Experience
)


def test_resume_schema():
    resume = Resume(
        name="Test Candidate",
        email="test@example.com",
        phone="+91 9000000000",
        skills=["Python", "SQL"],
        education=[
            Education(
                institution="Test University",
                degree="B.Tech",
                field_of_study="Computer Science",
                start_year=2023,
                end_year=2027
            )
        ],
        projects=[
            Project(
                title="Resume Screener",
                description="A resume screening project",
                technologies=["Python", "FastAPI"]
            )
        ],
        experience=[
            Experience(
                company="Test Company",
                role="Software Intern",
                start_date="2025",
                end_date="2026",
                description="Worked on backend development"
            )
        ],
        certifications=["Python Certification"],
        languages=["English"]
    )

    assert resume.name == "Test Candidate"
    assert "Python" in resume.skills
    assert len(resume.education) == 1
    assert len(resume.projects) == 1
    assert len(resume.experience) == 1