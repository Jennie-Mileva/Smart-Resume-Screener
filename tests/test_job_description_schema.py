from backend.app.schemas.job_description import JobDescription


def test_job_description_schema():
    jd = JobDescription(
        title="Python Backend Developer",
        required_skills=[
            "python",
            "fastapi",
            "postgresql",
            "sql",
            "docker",
            "git",
        ],
        preferred_skills=[
            "aws",
            "redis",
            "kubernetes",
        ],
        education_requirements=[
            "Bachelor's degree in Computer Science or related field."
        ],
        experience_requirements=[
            "1–2 years of experience in backend development."
        ],
        responsibilities=[
            "Develop and maintain backend services using Python.",
            "Design and build RESTful APIs using FastAPI.",
        ],
    )

    assert jd.title == "Python Backend Developer"

    assert "python" in jd.required_skills
    assert "fastapi" in jd.required_skills

    assert "aws" in jd.preferred_skills

    assert len(jd.education_requirements) == 1
    assert len(jd.experience_requirements) == 1
    assert len(jd.responsibilities) == 2