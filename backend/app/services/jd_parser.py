import re
from typing import Dict, List

from backend.app.schemas.job_description import JobDescription


SECTION_ALIASES = {
    "required_skills": {
        "required skills",
        "required skills & qualifications",
        "required qualifications",
        "must have",
        "mandatory skills",
        "technical skills",
    },
    "preferred_skills": {
        "preferred skills",
        "preferred qualifications",
        "nice to have",
        "nice-to-have",
        "desired skills",
        "bonus skills",
    },
    "education": {
        "education",
        "educational requirements",
        "education requirements",
        "qualifications",
        "academic requirements",
    },
    "experience": {
        "experience",
        "experience requirements",
        "required experience",
        "work experience",
        "professional experience",
    },
    "responsibilities": {
        "responsibilities",
        "key responsibilities",
        "job responsibilities",
        "what you'll do",
        "what you will do",
        "duties",
    },
}


def normalize_heading(line: str) -> str:
    """
    Normalize a section heading so different formatting
    can still be recognized.
    """

    cleaned = line.strip()

    # Remove common markdown heading markers.
    cleaned = re.sub(r"^#+\s*", "", cleaned)

    # Remove trailing colon.
    cleaned = re.sub(r":+$", "", cleaned)

    # Normalize whitespace.
    cleaned = re.sub(r"\s+", " ", cleaned)

    return cleaned.strip().lower()


def detect_section(line: str) -> str | None:
    """
    Return the internal section name for a JD heading.
    """

    normalized = normalize_heading(line)

    for section_name, aliases in SECTION_ALIASES.items():
        if normalized in aliases:
            return section_name

    return None


def extract_sections(text: str) -> Dict[str, str]:
    """
    Split a job description into logical sections.
    """

    sections: Dict[str, List[str]] = {}
    current_section = "header"

    sections[current_section] = []

    for raw_line in text.splitlines():
        line = raw_line.strip()

        if not line:
            continue

        section = detect_section(line)

        if section:
            current_section = section
            sections.setdefault(current_section, [])
            continue

        sections.setdefault(current_section, []).append(line)

    return {
        section: "\n".join(lines).strip()
        for section, lines in sections.items()
        if lines
    }


def clean_list_item(line: str) -> str:
    """
    Remove bullets and unnecessary whitespace.
    """

    cleaned = re.sub(
        r"^\s*(?:[-•*]|\d+[.)])\s*",
        "",
        line.strip(),
    )

    return cleaned.strip()


def parse_list(section_text: str) -> List[str]:
    """
    Convert a section into a list of individual items.

    Each line is treated as one item. Commas are preserved because
    they may separate parts of a single requirement or sentence.
    """

    if not section_text:
        return []

    items = []

    for line in section_text.splitlines():
        cleaned = clean_list_item(line)

        if cleaned:
            items.append(cleaned)

    return items

def parse_skill_list(section_text: str) -> List[str]:
    """
    Parse skills where multiple skills may appear on one line,
    separated by commas.
    """

    if not section_text:
        return []

    skills = []

    for line in section_text.splitlines():
        cleaned = clean_list_item(line)

        if not cleaned:
            continue

        parts = [part.strip() for part in cleaned.split(",")]

        for part in parts:
            if part:
                skills.append(part)

    return skills


def parse_required_skills(section_text: str) -> List[str]:
    return parse_skill_list(section_text)


def parse_preferred_skills(section_text: str) -> List[str]:
    return parse_skill_list(section_text)

def parse_education(section_text: str) -> List[str]:
    return parse_list(section_text)


def parse_experience(section_text: str) -> List[str]:
    return parse_list(section_text)


def parse_responsibilities(section_text: str) -> List[str]:
    return parse_list(section_text)


def extract_title(text: str, sections: Dict[str, str]) -> str | None:
    """
    Extract the job title from the beginning of the JD.

    We use the first meaningful line before the first recognized
    section heading.
    """

    header = sections.get("header", "")

    if not header:
        return None

    for line in header.splitlines():
        cleaned = line.strip()

        if cleaned:
            return cleaned

    return None


def parse_job_description(text: str) -> JobDescription:
    """
    Convert raw job description text into a validated
    JobDescription object.
    """

    sections = extract_sections(text)

    return JobDescription(
        title=extract_title(text, sections),
        required_skills=parse_required_skills(
            sections.get("required_skills", "")
        ),
        preferred_skills=parse_preferred_skills(
            sections.get("preferred_skills", "")
        ),
        education_requirements=parse_education(
            sections.get("education", "")
        ),
        experience_requirements=parse_experience(
            sections.get("experience", "")
        ),
        responsibilities=parse_responsibilities(
            sections.get("responsibilities", "")
        ),
    )




