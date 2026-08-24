from backend.app.services.resume_parser import parse_resume


def test_parse_resume():
    resume_text = """
    JENNIE MILEVA
    Kozhikode, Kerala, India
    +91 9188292650
    jenniemileva10@gmail.com

    EDUCATION
    VIT-AP University — B.Tech, CSE (Core) | 2023 – 2027

    TECHNICAL SKILLS
    Languages: Java, Python, C, JavaScript, SQL
    Web: React, Node.js, MongoDB, Flask

    PROJECTS
    IoT Smart Traffic Management System
    Aero Drone – Real-Time Aerial Monitoring System

    CERTIFICATIONS
    IBM Generative AI Course
    NPTEL Cyber Security and Privacy

    LANGUAGES
    English (Proficient) | Malayalam (Native) | Hindi (Proficient)
    """

    resume = parse_resume(resume_text)

    # Personal information
    assert resume.name == "JENNIE MILEVA"
    assert resume.email == "jenniemileva10@gmail.com"
    assert resume.phone == "+91 9188292650"

    # Skills
    assert "python" in resume.skills
    assert "java" in resume.skills
    assert "sql" in resume.skills
    assert "react" in resume.skills
    assert "mongodb" in resume.skills

    # Education
    assert len(resume.education) == 1
    assert resume.education[0].institution == "VIT-AP University"
    assert resume.education[0].degree == "B.Tech"
    assert resume.education[0].start_year == 2023
    assert resume.education[0].end_year == 2027

    # Projects
    assert len(resume.projects) == 2
    assert resume.projects[0].title == "IoT Smart Traffic Management System"
    assert resume.projects[1].title == "Aero Drone – Real-Time Aerial Monitoring System"

    # Certifications
    assert len(resume.certifications) == 2
    assert "IBM Generative AI Course" in resume.certifications

    # Languages
    assert len(resume.languages) == 3
    assert "English (Proficient)" in resume.languages