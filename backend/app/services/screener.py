from backend.app.schemas.job_description import JobDescription
from backend.app.services.llm_matcher import (
    llm_match_resume_to_job,
)


def classify_score(score: float) -> str:
    """
    Convert a numeric score into a screening classification.
    """

    if score >= 8:
        return "Strong Match"

    if score >= 6:
        return "Consider"

    return "Not Recommended"


def screen_candidates(
    candidates: list[dict],
    job_description: JobDescription,
) -> list[dict]:
    """
    Screen multiple candidates against one job description.

    Each candidate is sent to the LLM for evaluation.
    Results are classified and sorted from highest
    score to lowest score.
    """

    results = []

    for candidate in candidates:

        resume = candidate["resume"]
        filename = candidate["filename"]

        llm_result = llm_match_resume_to_job(
            resume,
            job_description,
        )

        score = float(
            llm_result.get("score", 0)
        )

        results.append(
            {
                "candidate_name": resume.name,
                "resume_filename": filename,
                "score": score,
                "classification": classify_score(score),
                "recommendation": llm_result.get(
                    "recommendation"
                ),
                "matched_skills": llm_result.get(
                    "matched_skills",
                    [],
                ),
                "missing_skills": llm_result.get(
                    "missing_skills",
                    [],
                ),
                "strengths": llm_result.get(
                    "strengths",
                    [],
                ),
                "justification": llm_result.get(
                    "justification",
                    "",
                ),
            }
        )

    # Highest score first
    results.sort(
        key=lambda item: item["score"],
        reverse=True,
    )

    # Add ranking
    for index, result in enumerate(
        results,
        start=1,
    ):
        result["rank"] = index

    return results