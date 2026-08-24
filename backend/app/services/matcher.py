import re

from backend.app.schemas.job_description import JobDescription
from backend.app.schemas.match import (
    MatchResult,
    SkillMatchResult,
    ExperienceMatchResult,
    EducationMatchResult,
    ProjectMatchResult,
)
from backend.app.schemas.resume import Resume


# ============================================================
# GENERAL HELPERS
# ============================================================

def normalize_skill(skill: str) -> str:
    """Normalize text for reliable comparison."""

    return " ".join(
        skill.lower().strip().split()
    )


def calculate_percentage(
    matched: int,
    total: int,
) -> float:
    """Calculate a percentage safely."""

    if total == 0:
        return 0.0

    return round(
        (matched / total) * 100,
        2,
    )


# ============================================================
# SKILL MATCHING
# ============================================================

def match_skills(
    resume: Resume,
    job_description: JobDescription,
) -> SkillMatchResult:
    """
    Match resume skills against required and preferred JD skills.
    """

    resume_skills = {
        normalize_skill(skill)
        for skill in resume.skills
    }

    required_skills = [
        skill.strip()
        for skill in job_description.required_skills
        if skill.strip()
    ]

    preferred_skills = [
        skill.strip()
        for skill in job_description.preferred_skills
        if skill.strip()
    ]

    matched_required = []
    missing_required = []

    for skill in required_skills:
        if normalize_skill(skill) in resume_skills:
            matched_required.append(skill)
        else:
            missing_required.append(skill)

    matched_preferred = []
    missing_preferred = []

    for skill in preferred_skills:
        if normalize_skill(skill) in resume_skills:
            matched_preferred.append(skill)
        else:
            missing_preferred.append(skill)

    return SkillMatchResult(
        matched_required_skills=matched_required,
        missing_required_skills=missing_required,
        matched_preferred_skills=matched_preferred,
        missing_preferred_skills=missing_preferred,
        required_match_percentage=calculate_percentage(
            len(matched_required),
            len(required_skills),
        ),
        preferred_match_percentage=calculate_percentage(
            len(matched_preferred),
            len(preferred_skills),
        ),
    )


# ============================================================
# EXPERIENCE MATCHING
# ============================================================

def match_experience(
    resume: Resume,
    job_description: JobDescription,
) -> ExperienceMatchResult:
    """
    Match JD experience requirements against resume experience.

    A requirement is considered matched when at least 50% of its
    meaningful keywords are present in the candidate's experience.
    """

    requirements = [
        requirement.strip()
        for requirement in job_description.experience_requirements
        if requirement.strip()
    ]

    if not requirements:
        return ExperienceMatchResult(
            matched=True,
            match_percentage=100.0,
            details=[
                "No specific experience requirement found in JD."
            ],
        )

    resume_text_parts = []

    for experience in resume.experience:

        if experience.role:
            resume_text_parts.append(
                experience.role
            )

        if experience.company:
            resume_text_parts.append(
                experience.company
            )

        if experience.description:
            resume_text_parts.append(
                experience.description
            )

    resume_text = normalize_skill(
        " ".join(resume_text_parts)
    )

    stop_words = {
        "experience",
        "years",
        "year",
        "building",
        "build",
        "developing",
        "developed",
        "development",
        "using",
        "work",
        "working",
        "with",
        "and",
        "the",
        "in",
        "of",
        "for",
        "to",
        "a",
        "an",
        "or",
        "on",
        "as",
    }

    matched_requirements = []
    missing_requirements = []

    for requirement in requirements:

        words = re.findall(
            r"[a-zA-Z0-9+#.-]+",
            requirement.lower(),
        )

        meaningful_words = [
            word
            for word in words
            if word not in stop_words
            and len(word) >= 3
        ]

        if not meaningful_words:
            missing_requirements.append(
                requirement
            )
            continue

        matched_words = [
            word
            for word in meaningful_words
            if word in resume_text
        ]

        ratio = (
            len(matched_words)
            / len(meaningful_words)
        )

        if ratio >= 0.5:
            matched_requirements.append(
                requirement
            )
        else:
            missing_requirements.append(
                requirement
            )

    percentage = calculate_percentage(
        len(matched_requirements),
        len(requirements),
    )

    details = []

    for requirement in matched_requirements:
        details.append(
            f"Matched experience requirement: {requirement}"
        )

    for requirement in missing_requirements:
        details.append(
            f"Missing experience requirement: {requirement}"
        )

    return ExperienceMatchResult(
        matched=bool(matched_requirements),
        match_percentage=percentage,
        details=details,
    )


# ============================================================
# EDUCATION MATCHING
# ============================================================

def match_education(
    resume: Resume,
    job_description: JobDescription,
) -> EducationMatchResult:
    """
    Match resume education against JD education requirements.

    Supports common degree equivalents:

    Bachelor's:
        B.Tech
        B.E.
        B.Sc.
        BCA

    Master's:
        M.Tech
        M.E.
        M.Sc.
        MCA
        MBA
    """

    requirements = [
        requirement.strip()
        for requirement in job_description.education_requirements
        if requirement.strip()
    ]

    if not requirements:
        return EducationMatchResult(
            matched=True,
            match_percentage=100.0,
            details=[
                "No specific education requirement found in JD."
            ],
        )

    matched_requirements = []
    missing_requirements = []

    for requirement in requirements:

        requirement_lower = requirement.lower()

        requires_bachelors = any(
            value in requirement_lower
            for value in [
                "bachelor",
                "bachelors",
                "bachelor's",
                "b.tech",
                "btech",
                "b.e",
                "b.sc",
                "bca",
            ]
        )

        requires_masters = any(
            value in requirement_lower
            for value in [
                "master",
                "masters",
                "master's",
                "m.tech",
                "mtech",
                "m.e",
                "m.sc",
                "mca",
                "mba",
            ]
        )

        requires_cs_or_it = any(
            value in requirement_lower
            for value in [
                "computer science",
                "computer science engineering",
                "cse",
                "information technology",
            ]
        )

        requirement_matched = False

        for education in resume.education:

            degree = normalize_skill(
                education.degree or ""
            )

            field = normalize_skill(
                education.field_of_study or ""
            )

            resume_is_bachelors = any(
                value in degree
                for value in [
                    "b.tech",
                    "btech",
                    "b.e",
                    "b.e.",
                    "be ",
                    "b.sc",
                    "bsc",
                    "bca",
                    "bachelor",
                ]
            )

            resume_is_masters = any(
                value in degree
                for value in [
                    "m.tech",
                    "mtech",
                    "m.e",
                    "m.e.",
                    "m.sc",
                    "msc",
                    "mca",
                    "mba",
                    "master",
                ]
            )

            if requires_bachelors:
                degree_matches = resume_is_bachelors
            elif requires_masters:
                degree_matches = resume_is_masters
            else:
                degree_matches = True

            if requires_cs_or_it:
                field_matches = any(
                    value in field
                    for value in [
                        "computer science",
                        "cse",
                        "information technology",
                    ]
                )
            else:
                field_matches = True

            if degree_matches and field_matches:
                requirement_matched = True
                break

        if requirement_matched:
            matched_requirements.append(
                requirement
            )
        else:
            missing_requirements.append(
                requirement
            )

    percentage = calculate_percentage(
        len(matched_requirements),
        len(requirements),
    )

    details = []

    for requirement in matched_requirements:
        details.append(
            f"Matched education requirement: {requirement}"
        )

    for requirement in missing_requirements:
        details.append(
            f"Missing education requirement: {requirement}"
        )

    return EducationMatchResult(
        matched=bool(matched_requirements),
        match_percentage=percentage,
        details=details,
    )


# ============================================================
# PROJECT MATCHING
# ============================================================

def normalize_project_text(text: str) -> str:
    """Normalize project text."""

    return " ".join(
        text.lower().strip().split()
    )


def project_contains_term(
    project_text: str,
    term: str,
) -> bool:
    """
    Check whether a project contains a JD technical term.
    """

    project_text = normalize_project_text(
        project_text
    )

    term = normalize_project_text(
        term
    )

    if not term:
        return False

    # Phrases such as:
    # machine learning
    # object-oriented programming
    if " " in term:
        return term in project_text

    pattern = (
        r"(?<!\w)"
        + re.escape(term)
        + r"(?!\w)"
    )

    return bool(
        re.search(
            pattern,
            project_text,
        )
    )


def match_projects(
    resume: Resume,
    job_description: JobDescription,
) -> ProjectMatchResult:
    """
    Match resume projects against technical JD skills.

    Projects are matched primarily using explicit technical
    skills rather than generic English words.
    """

    technical_terms = []

    # Required + preferred skills are the strongest signals.
    technical_terms.extend(
        job_description.required_skills
    )

    technical_terms.extend(
        job_description.preferred_skills
    )

    # Additional technical terms that can appear inside
    # responsibilities.
    known_terms = {
        "python",
        "fastapi",
        "flask",
        "django",
        "rest",
        "rest api",
        "rest apis",
        "restful api",
        "restful apis",
        "postgresql",
        "postgres",
        "sql",
        "mysql",
        "mongodb",
        "docker",
        "kubernetes",
        "aws",
        "azure",
        "gcp",
        "redis",
        "react",
        "node",
        "node.js",
        "javascript",
        "typescript",
        "java",
        "c++",
        "machine learning",
        "deep learning",
        "nlp",
        "computer vision",
        "git",
        "github",
        "object-oriented programming",
        "data structures",
        "algorithms",
    }

    responsibility_text = normalize_project_text(
        " ".join(
            job_description.responsibilities
        )
    )

    for term in known_terms:
        if project_contains_term(
            responsibility_text,
            term,
        ):
            technical_terms.append(term)

    # Normalize + remove duplicates.
    normalized_terms = []

    for term in technical_terms:

        normalized = normalize_skill(
            term
        )

        if (
            normalized
            and normalized not in normalized_terms
        ):
            normalized_terms.append(
                normalized
            )

    if not normalized_terms:
        return ProjectMatchResult(
            matched_projects=[],
            match_percentage=0.0,
            details=[
                "No project-related information found in JD."
            ],
        )

    matched_projects = []
    details = []

    for project in resume.projects:

        parts = []

        if project.title:
            parts.append(
                project.title
            )

        if project.description:
            parts.append(
                project.description
            )

        parts.extend(
            project.technologies
        )

        project_text = normalize_project_text(
            " ".join(parts)
        )

        matched_terms = []

        for term in normalized_terms:

            if project_contains_term(
                project_text,
                term,
            ):
                matched_terms.append(
                    term
                )

        if matched_terms:

            matched_projects.append(
                project.title
            )

            details.append(
                f"Matched project: {project.title} "
                f"(matched: {', '.join(matched_terms)})"
            )

    percentage = calculate_percentage(
        len(matched_projects),
        len(resume.projects),
    )

    if not matched_projects:
        details.append(
            "No projects matched the job description."
        )

    return ProjectMatchResult(
        matched_projects=matched_projects,
        match_percentage=percentage,
        details=details,
    )


# ============================================================
# OVERALL SCORE
# ============================================================

# ============================================================
# OVERALL SCORE
# ============================================================

def calculate_overall_score(
    skill_match: SkillMatchResult,
) -> float:
    """
    Calculate the overall resume-to-JD score.

    Required skills : 80%
    Preferred skills: 20%

    Experience, education, and projects are calculated
    separately and are not included in the overall score yet.
    """

    required_score = (
        skill_match.required_match_percentage
    )

    preferred_score = (
        skill_match.preferred_match_percentage
    )

    score = (
        required_score * 0.80
        + preferred_score * 0.20
    )

    return round(
        score,
        2,
    )

# ============================================================
# COMPLETE MATCH
# ============================================================

def match_resume_to_job(
    resume: Resume,
    job_description: JobDescription,
) -> MatchResult:
    """
    Match a complete resume against a complete job description.
    """

    skill_match = match_skills(
        resume,
        job_description,
    )

    experience_match = match_experience(
        resume,
        job_description,
    )

    education_match = match_education(
        resume,
        job_description,
    )

    project_match = match_projects(
        resume,
        job_description,
    )

    overall_score = calculate_overall_score(
        skill_match
    )

    return MatchResult(
        candidate_name=resume.name,
        skill_match=skill_match,
        experience_match=experience_match,
        education_match=education_match,
        project_match=project_match,
        overall_score=overall_score,
    )