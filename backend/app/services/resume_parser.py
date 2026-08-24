import re
from typing import Dict, List

from backend.app.schemas.resume import (
    Education,
    Experience,
    Project,
    Resume,
)


COMMON_SKILLS = {
    "python",
    "java",
    "javascript",
    "typescript",
    "c",
    "c++",
    "c#",
    "sql",
    "html",
    "css",
    "react",
    "node.js",
    "node",
    "express",
    "mongodb",
    "flask",
    "django",
    "fastapi",
    "machine learning",
    "deep learning",
    "nlp",
    "computer vision",
    "aws",
    "azure",
    "docker",
    "git",
    "github",
    "tensorflow",
    "pytorch",
}


SECTION_ALIASES = {
    "education": {
        "education",
        "academic background",
        "academic qualifications",
    },
    "skills": {
        "technical skills",
        "skills",
        "technical expertise",
        "core skills",
    },
    "projects": {
        "projects",
        "academic projects",
        "personal projects",
    },
    "experience": {
        "experience",
        "work experience",
        "professional experience",
        "internship",
        "internships",
    },
    "certifications": {
        "certifications",
        "certificates",
        "courses & certifications",
    },
    "languages": {
        "languages",
        "language proficiency",
    },
    "leadership": {
        "leadership & extracurricular",
        "leadership",
        "extracurricular",
        "activities",
    },
}


def extract_email(text: str) -> str | None:
    """Extract the first email address from resume text."""

    match = re.search(
        r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
        text,
    )

    return match.group(0) if match else None


def extract_phone(text: str) -> str | None:
    """Extract a likely phone number from resume text."""

    match = re.search(
        r"(?:\+?\d[\d\s().-]{8,}\d)",
        text,
    )

    if not match:
        return None

    phone = match.group(0).strip()

    digits = re.sub(r"\D", "", phone)

    if 10 <= len(digits) <= 15:
        return phone

    return None


def extract_name(text: str) -> str | None:
    """Extract a likely candidate name from the beginning of the resume."""

    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    if not lines:
        return None

    for line in lines[:10]:
        lower_line = line.lower()

        if "@" in line:
            continue

        if re.search(r"\d", line):
            continue

        if any(
            keyword in lower_line
            for keyword in [
                "linkedin",
                "github",
                "leetcode",
                "resume",
                "curriculum vitae",
            ]
        ):
            continue

        words = line.split()

        if 2 <= len(words) <= 5:
            return line

    return None


def extract_skills(text: str) -> List[str]:
    """Extract skills from the controlled vocabulary."""

    text_lower = text.lower()

    found_skills = []

    for skill in COMMON_SKILLS:
        pattern = r"(?<!\w)" + re.escape(skill) + r"(?!\w)"

        if re.search(pattern, text_lower):
            found_skills.append(skill)

    return sorted(found_skills)


def normalize_section_heading(line: str) -> str | None:
    """Convert a resume section heading into a normalized section name."""

    cleaned = re.sub(r"[:\-]+$", "", line.strip())
    cleaned = re.sub(r"\s+", " ", cleaned).strip().lower()

    for section_name, aliases in SECTION_ALIASES.items():
        if cleaned in aliases:
            return section_name

    return None


def extract_sections(text: str) -> Dict[str, str]:
    """Split the resume into logical sections."""

    sections: Dict[str, List[str]] = {}

    current_section = "header"

    sections[current_section] = []

    for raw_line in text.splitlines():
        line = raw_line.strip()

        if not line:
            continue

        section_name = normalize_section_heading(line)

        if section_name:
            current_section = section_name
            sections.setdefault(current_section, [])
            continue

        sections.setdefault(current_section, []).append(line)

    return {
        section: "\n".join(lines).strip()
        for section, lines in sections.items()
        if lines
    }


def parse_education(section_text: str) -> List[Education]:
    """Extract basic education information."""

    if not section_text:
        return []

    entries = []

    for line in section_text.splitlines():
        line = line.strip()

        if not line:
            continue

        year_matches = re.findall(
            r"\b(?:19|20)\d{2}\b",
            line,
        )

        start_year = None
        end_year = None

        if len(year_matches) >= 2:
            start_year = int(year_matches[0])
            end_year = int(year_matches[1])

        elif len(year_matches) == 1:
            end_year = int(year_matches[0])

        degree_match = re.search(
            r"\b(B\.?Tech|B\.?E|M\.?Tech|M\.?E|B\.?Sc|M\.?Sc|"
            r"BCA|MCA|MBA|Ph\.?D|Bachelor(?:'s)?|Master(?:'s)?)\b",
            line,
            re.IGNORECASE,
        )

        degree = degree_match.group(0) if degree_match else None

        institution = line

        if "—" in line:
            institution = line.split("—", 1)[0].strip()

        elif " - " in line:
            institution = line.split(" - ", 1)[0].strip()

        field_of_study = None

        if degree_match:
            after_degree = line[degree_match.end():]

            after_degree = after_degree.split("|")[0]
            after_degree = after_degree.strip(" ,:-")

            if after_degree:
                field_of_study = after_degree

        entries.append(
            Education(
                institution=institution,
                degree=degree,
                field_of_study=field_of_study,
                start_year=start_year,
                end_year=end_year,
            )
        )

    return entries


def is_project_title(line: str) -> bool:
    """
    Identify likely project-title lines.

    A year at the end of a line is the strongest signal.

    For resumes where project years are omitted, short lines
    that do not look like normal description sentences can
    also be project titles.
    """

    stripped = line.strip()

    if not stripped:
        return False

    # Explicit bullet lines are descriptions, not titles.
    if stripped.startswith(("•", "-", "*")):
        return False

    # A year at the end is a strong project-title signal.
    if re.search(
        r"\b(?:19|20)\d{2}\b\s*$",
        stripped,
    ):
        return True

    # Common words that indicate a description sentence.
    description_starters = (
        "built ",
        "developed ",
        "enabled ",
        "created ",
        "implemented ",
        "designed ",
        "integrated ",
        "deployed ",
        "used ",
        "automated ",
        "exported ",
    )

    lower = stripped.lower()

    if lower.startswith(description_starters):
        return False

    # Lines ending with punctuation are more likely to be
    # wrapped description text than project titles.
    if stripped.endswith((".", ",", ";", ":")):
        return False

    # If there is no year, allow reasonably short title-like lines.
    return len(stripped.split()) <= 10


def clean_project_title(line: str) -> str:
    """Remove a trailing year from a project title."""

    title = re.sub(
        r"\b(?:19|20)\d{2}\b",
        "",
        line,
    )

    return re.sub(
        r"\s+",
        " ",
        title,
    ).strip(" -–—")


def parse_projects(section_text: str) -> List[Project]:
    """
    Parse projects while preserving wrapped PDF text.

    PDF extraction frequently breaks one bullet into multiple
    physical lines. Therefore, everything between two project
    headings belongs to the current project.
    """

    if not section_text:
        return []

    projects: List[Project] = []

    current_title = None
    current_description: List[str] = []

    def save_current_project():
        nonlocal current_title
        nonlocal current_description

        if current_title is None:
            return

        description = " ".join(
            current_description
        ).strip()

        technologies = []

        description_lower = description.lower()

        for skill in COMMON_SKILLS:
            pattern = (
                r"(?<!\w)"
                + re.escape(skill)
                + r"(?!\w)"
            )

            if re.search(
                pattern,
                description_lower,
            ):
                technologies.append(skill)

        projects.append(
            Project(
                title=current_title,
                description=description or None,
                technologies=sorted(technologies),
            )
        )

        current_title = None
        current_description = []

    for raw_line in section_text.splitlines():

        line = raw_line.strip()

        if not line:
            continue

        # Remove PDF bullet characters.
        cleaned_line = re.sub(
            r"^[•\-\*]\s*",
            "",
            line,
        ).strip()

        # Check the original line for title detection.
        if is_project_title(line):

            # Save the previous project before starting
            # a new one.
            save_current_project()

            current_title = clean_project_title(
                cleaned_line
            )

            continue

        # Any non-title line belongs to the current project.
        if current_title is not None:
            current_description.append(
                cleaned_line
            )

    # Save the final project.
    save_current_project()

    return projects


def parse_experience(section_text: str) -> List[Experience]:
    """
    Basic experience parser.

    Experience parsing will be expanded when we introduce
    JD-aware matching and support for more resume formats.
    """

    if not section_text:
        return []

    return []


def parse_certifications(section_text: str) -> List[str]:
    """Extract certifications, including pipe-separated entries."""

    if not section_text:
        return []

    certifications = []

    for line in section_text.splitlines():

        parts = re.split(
            r"\s*\|\s*",
            line,
        )

        for part in parts:

            certification = re.sub(
                r"^[•\-\*]\s*",
                "",
                part.strip(),
            )

            if certification:
                certifications.append(
                    certification
                )

    return certifications


def parse_languages(section_text: str) -> List[str]:
    """Extract languages from the languages section."""

    if not section_text:
        return []

    languages = []

    for line in section_text.splitlines():

        parts = re.split(
            r"\||,",
            line,
        )

        for part in parts:

            language = part.strip()

            if language:
                languages.append(
                    language
                )

    return languages


def parse_resume(text: str) -> Resume:
    """Convert raw resume text into a validated Resume object."""

    sections = extract_sections(text)

    return Resume(
        name=extract_name(text),
        email=extract_email(text),
        phone=extract_phone(text),
        skills=extract_skills(text),

        education=parse_education(
            sections.get(
                "education",
                "",
            )
        ),

        experience=parse_experience(
            sections.get(
                "experience",
                "",
            )
        ),

        projects=parse_projects(
            sections.get(
                "projects",
                "",
            )
        ),

        certifications=parse_certifications(
            sections.get(
                "certifications",
                "",
            )
        ),

        languages=parse_languages(
            sections.get(
                "languages",
                "",
            )
        ),
    )