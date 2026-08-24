from backend.app.schemas.job_description import JobDescription
from backend.app.schemas.match import MatchResult, SkillMatchResult
from backend.app.schemas.resume import Resume


def normalize_skill(skill: str) -> str:
    """
    Normalize a skill for comparison.

    This allows differences such as:
    Python
    python
    PYTHON

    to be treated as the same skill.
    """

    return " ".join(skill.lower().strip().split())


def calculate_percentage(matched: int, total: int) -> float:
    """
    Calculate a percentage safely.
    """

    if total == 0:
        return 0.0

    return round((matched / total) * 100, 2)


def match_skills(
    resume: Resume,
    job_description: JobDescription,
) -> SkillMatchResult:
    """
    Compare resume skills against JD required and preferred skills.
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

    required_percentage = calculate_percentage(
        len(matched_required),
        len(required_skills),
    )

    preferred_percentage = calculate_percentage(
        len(matched_preferred),
        len(preferred_skills),
    )

    return SkillMatchResult(
        matched_required_skills=matched_required,
        missing_required_skills=missing_required,
        matched_preferred_skills=matched_preferred,
        missing_preferred_skills=missing_preferred,
        required_match_percentage=required_percentage,
        preferred_match_percentage=preferred_percentage,
    )


def calculate_overall_score(
    skill_match: SkillMatchResult,
) -> float:
    """
    Calculate the initial overall score.

    Required skills have higher importance than preferred skills.

    Current weighting:
        Required skills: 80%
        Preferred skills: 20%
    """

    required_score = skill_match.required_match_percentage
    preferred_score = skill_match.preferred_match_percentage

    # If the JD has no preferred skills, use required skills only.
    if (
        not skill_match.matched_preferred_skills
        and not skill_match.missing_preferred_skills
    ):
        return round(required_score, 2)

    score = (
        required_score * 0.80
        + preferred_score * 0.20
    )

    return round(score, 2)


def match_resume_to_job(
    resume: Resume,
    job_description: JobDescription,
) -> MatchResult:
    """
    Match a parsed resume against a parsed job description.
    """

    skill_match = match_skills(
        resume,
        job_description,
    )

    overall_score = calculate_overall_score(
        skill_match,
    )

    return MatchResult(
        candidate_name=resume.name,
        skill_match=skill_match,
        overall_score=overall_score,
    )