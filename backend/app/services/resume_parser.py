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
    Parse work experience from PDF-extracted resume text.

    Supports:
    - company + location + company description + role + date
    - role + date
    - dates split across PDF lines
    - bullet-point descriptions
    - previous-experience sections
    """

    if not section_text:
        return []

    lines = [
        line.strip()
        for line in section_text.splitlines()
        if line.strip()
    ]

    # Remove PDF bullet-only lines and normalize bullets.
    cleaned_lines = []

    for line in lines:
        line = re.sub(
            r"^[●•ΓÇó]\s*",
            "",
            line,
        ).strip()

        if line:
            cleaned_lines.append(line)

    lines = cleaned_lines

    # Normal date range:
    # 01/2022 – Present
    # 10/2019 – 12/2021
    date_pattern = re.compile(
        r"^\s*"
        r"(?P<start>(?:\d{1,2}/)?(?:19|20)\d{2})"
        r"\s*[-–—]\s*"
        r"(?P<end>(?:\d{1,2}/)?(?:19|20)\d{2}|Present)"
        r"\s*$",
        re.IGNORECASE,
    )

    # Split date:
    # 01/2016
    # – 05/2017
    split_date_start = re.compile(
        r"^\s*(?:\d{1,2}/)?(?:19|20)\d{2}\s*$"
    )

    split_date_end = re.compile(
        r"^\s*[-–—]\s*"
        r"(?:\d{1,2}/)?(?:19|20)\d{2}"
        r"\s*$"
    )

    # First convert split dates into one line.
    normalized_lines = []

    i = 0

    while i < len(lines):

        if (
            split_date_start.match(lines[i])
            and i + 1 < len(lines)
            and split_date_end.match(lines[i + 1])
        ):
            normalized_lines.append(
                f"{lines[i]} {lines[i + 1]}"
            )

            i += 2
            continue

        normalized_lines.append(lines[i])
        i += 1

    lines = normalized_lines

    # Find all date positions.
    date_positions = []

    for index, line in enumerate(lines):

        match = date_pattern.match(line)

        if match:
            date_positions.append(
                (
                    index,
                    match.group("start"),
                    match.group("end"),
                )
            )

    experiences = []

    # Words that strongly indicate a company description.
    description_indicators = (
        "startup",
        "company",
        "recruitment",
        "employer",
        "saas",
        "users",
        "listed",
        "revenue",
        "training",
        "membership",
        "platform",
        "software",
        "technology",
        "technologies",
    )

    # Words that indicate a location.
    location_pattern = re.compile(
        r",\s*(?:United Kingdom|UK|USA|US|India|"
        r"Canada|Australia|Germany|France|Spain|"
        r"New York|London|California)",
        re.IGNORECASE,
    )

    for position_index, (
        date_index,
        start_date,
        end_date,
    ) in enumerate(date_positions):

        # Everything before this date.
        previous_start = (
            date_positions[position_index - 1][0] + 1
            if position_index > 0
            else 0
        )

        block_before_date = lines[
            previous_start:date_index
        ]

        if not block_before_date:
            continue

        # --------------------------------------------------
        # DETERMINE ROLE AND COMPANY
        # --------------------------------------------------

        role = block_before_date[-1]
        company = None

        # Previous-experience format:
        #
        # Coder,
        # ABC Company, London, UK
        # 06/2017 – 10/2018
        #
        # Ethical Hacker,
        # XYZ Company, New York, USA
        # 01/2016 – 05/2017
        #
        # In this format:
        #   block_before_date[-2] = role
        #   block_before_date[-1] = company + location

        if (
            len(block_before_date) >= 2
            and "," in block_before_date[-1]
        ):
            possible_role = block_before_date[-2].strip(
                " ,-"
            )

            possible_company = block_before_date[-1].strip(
                " ,-"
            )

            if (
                possible_role
                and possible_company
            ):
                role = possible_role
                company = possible_company

        # --------------------------------------------------
        # NORMAL EXPERIENCE FORMAT
        # --------------------------------------------------

        if company is None:

            # The role is normally immediately before
            # the date.
            role = block_before_date[-1]

            # Search backwards for the company.
            for candidate in reversed(
                block_before_date[:-1]
            ):

                candidate_clean = candidate.strip(
                    " ,-"
                )

                lower_candidate = (
                    candidate_clean.lower()
                )

                # Ignore company-description lines.
                if any(
                    indicator in lower_candidate
                    for indicator in description_indicators
                ):
                    continue

                # Ignore location-only lines.
                if (
                    location_pattern.search(
                        candidate_clean
                    )
                    and len(
                        candidate_clean.split()
                    ) <= 6
                ):
                    continue

                # Ignore separator lines.
                if set(candidate_clean) <= {
                    "_",
                    "-",
                    "–",
                    "—",
                }:
                    continue

                company = candidate_clean
                break

        if not company:
            company = "Unknown"

        # --------------------------------------------------
        # DESCRIPTION
        # --------------------------------------------------

        next_date_index = (
            date_positions[position_index + 1][0]
            if position_index + 1 < len(date_positions)
            else len(lines)
        )

        description_lines = lines[
            date_index + 1:next_date_index
        ]

        # Stop description when the next company block
        # starts.
        if description_lines:

            stop_index = len(description_lines)

            for j in range(
                len(description_lines) - 1
            ):

                current = description_lines[j]
                following = description_lines[j + 1]

                # A location line often contains a comma.
                looks_like_location = (
                    "," in following
                    and len(following.split()) <= 8
                )

                # Avoid treating normal bullet/description
                # text as a company name.
                looks_like_company = (
                    not current.endswith(".")
                    and not current.startswith(
                        (
                            "Created ",
                            "Developed ",
                            "Supervised ",
                            "Designed ",
                            "Implemented ",
                            "Launched ",
                            "Responded ",
                            "Provided ",
                            "Discovered ",
                            "Answered ",
                        )
                    )
                )

                if (
                    looks_like_company
                    and looks_like_location
                ):
                    stop_index = j
                    break

            description_lines = description_lines[
                :stop_index
            ]

        description_parts = []

        for line in description_lines:

            upper_line = line.upper()

            # Skip section/contact headings.
            if upper_line in {
                "PREVIOUS EXPERIENCE",
                "CONTACT",
                "SKILLS",
                "EDUCATION",
                "OTHER",
            }:
                continue

            # Skip separator lines.
            if set(line) <= {
                "_",
                "-",
                "–",
                "—",
            }:
                continue

            description_parts.append(line)

        description = " ".join(
            description_parts
        ).strip()

        experiences.append(
            Experience(
                company=company,
                role=role,
                start_date=start_date,
                end_date=end_date,
                description=(
                    description
                    if description
                    else None
                ),
            )
        )

    return experiences
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