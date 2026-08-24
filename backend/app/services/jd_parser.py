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

    # We recognize this section so it does NOT get
    # accidentally added to preferred skills.
    "nice_to_have": {
        "nice to have",
        "nice-to-have",
    },
}


def normalize_heading(line: str) -> str:
    cleaned = line.strip()

    cleaned = re.sub(r"^#+\s*", "", cleaned)
    cleaned = re.sub(r":+$", "", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned)

    return cleaned.strip().lower()


def detect_section(line: str) -> str | None:
    normalized = normalize_heading(line)

    for section_name, aliases in SECTION_ALIASES.items():
        if normalized in aliases:
            return section_name

    return None


def extract_sections(text: str) -> Dict[str, str]:
    """
    Split JD into logical sections.

    Supports:

        Required Skills
        - Python
        - FastAPI

    and PDF-extracted formats such as:

        Required Skills - Python - FastAPI - SQL
    """

    sections: Dict[str, List[str]] = {}
    current_section = "header"

    sections[current_section] = []

    for raw_line in text.splitlines():

        line = raw_line.strip()

        if not line:
            continue

        # --------------------------------------------
        # Normal section heading
        # --------------------------------------------

        section = detect_section(line)

        if section:
            current_section = section
            sections.setdefault(current_section, [])
            continue

        # --------------------------------------------
        # Inline section heading
        #
        # Example:
        # Required Skills - Python - FastAPI
        # --------------------------------------------

        matched_section = None
        inline_content = None

        normalized_line = normalize_heading(line)

        for section_name, aliases in SECTION_ALIASES.items():

            for alias in aliases:

                pattern = (
                    r"^"
                    + re.escape(alias)
                    + r"\s*[-:]\s*(.+)$"
                )

                match = re.match(
                    pattern,
                    normalized_line,
                    re.IGNORECASE,
                )

                if match:
                    matched_section = section_name
                    inline_content = match.group(1).strip()
                    break

            if matched_section:
                break

        if matched_section:

            current_section = matched_section

            sections.setdefault(
                current_section,
                [],
            )

            if inline_content:
                sections[current_section].append(
                    inline_content
                )

            continue

        # --------------------------------------------
        # Normal content
        # --------------------------------------------

        sections.setdefault(
            current_section,
            [],
        )

        sections[current_section].append(line)

    return {
        section: "\n".join(lines).strip()
        for section, lines in sections.items()
        if lines
    }


def clean_list_item(line: str) -> str:
    """
    Remove common bullet characters.
    """

    cleaned = line.strip()

    cleaned = re.sub(
        r"^(?:[-*•ΓÇó]\s*)+",
        "",
        cleaned,
    )

    cleaned = re.sub(
        r"^\d+[.)]\s*",
        "",
        cleaned,
    )

    return cleaned.strip()


def split_bullets(text: str) -> List[str]:
    """
    Split both real newline bullets and PDF-extracted
    inline bullets.

    Example:

    - Python - FastAPI - SQL

    becomes:

    Python
    FastAPI
    SQL
    """

    if not text:
        return []

    items = []

    for line in text.splitlines():

        line = line.strip()

        if not line:
            continue

        # Normalize PDF bullet characters.
        line = line.replace("ΓÇó", "-")
        line = line.replace("•", "-")

        # --------------------------------------------
        # If the line contains multiple bullet items
        # --------------------------------------------

        parts = re.split(
            r"\s+-\s+",
            line,
        )

        for part in parts:

            cleaned = clean_list_item(part)

            if cleaned:
                items.append(cleaned)

    return items


def parse_list(section_text: str) -> List[str]:
    """
    Parse normal requirement/responsibility lists.

    Each bullet becomes one item.
    """

    return split_bullets(section_text)


def parse_skill_list(section_text: str) -> List[str]:
    """
    Parse skill lists.

    Supports:

        Python
        FastAPI

    and:

        Python, FastAPI, SQL

    and:

        Python - FastAPI - SQL
    """

    if not section_text:
        return []

    skills = []

    items = split_bullets(section_text)

    for item in items:

        # Comma-separated skills.
        comma_parts = item.split(",")

        for part in comma_parts:

            skill = part.strip()

            if skill:
                skills.append(skill)

    return skills


def parse_required_skills(
    section_text: str,
) -> List[str]:

    return parse_skill_list(section_text)


def parse_preferred_skills(
    section_text: str,
) -> List[str]:

    return parse_skill_list(section_text)


def parse_education(
    section_text: str,
) -> List[str]:

    return parse_list(section_text)


def parse_experience(
    section_text: str,
) -> List[str]:

    return parse_list(section_text)


def parse_responsibilities(
    section_text: str,
) -> List[str]:

    return parse_list(section_text)


def extract_title(
    text: str,
    sections: Dict[str, str],
) -> str | None:

    header = sections.get("header", "")

    if not header:
        return None

    for line in header.splitlines():

        cleaned = line.strip()

        if cleaned:
            return cleaned

    return None


def parse_job_description(
    text: str,
) -> JobDescription:

    sections = extract_sections(text)

    return JobDescription(
        title=extract_title(
            text,
            sections,
        ),

        required_skills=parse_required_skills(
            sections.get(
                "required_skills",
                "",
            )
        ),

        preferred_skills=parse_preferred_skills(
            sections.get(
                "preferred_skills",
                "",
            )
        ),

        education_requirements=parse_education(
            sections.get(
                "education",
                "",
            )
        ),

        experience_requirements=parse_experience(
            sections.get(
                "experience",
                "",
            )
        ),

        responsibilities=parse_responsibilities(
            sections.get(
                "responsibilities",
                "",
            )
        ),
    )