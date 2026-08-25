from backend.app.schemas.job_description import JobDescription
from backend.app.services.llm_matcher import (
    llm_match_resume_to_job,
)
from backend.app.services.matcher import (
    match_resume_to_job,
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

    Gemini is used when available.

    If the LLM is unavailable, for example because of
    quota/rate-limit errors, the deterministic matcher
    is used as a fallback so screening can continue.
    """

    results = []

    for candidate in candidates:

        resume = candidate["resume"]
        filename = candidate["filename"]

        # --------------------------------------------------
        # 1. Try LLM matching
        # --------------------------------------------------

        try:
            llm_result = llm_match_resume_to_job(
                resume,
                job_description,
            )

            score = float(
                llm_result.get("score", 0)
            )

            recommendation = llm_result.get(
                "recommendation"
            )

            matched_skills = llm_result.get(
                "matched_skills",
                [],
            )

            missing_skills = llm_result.get(
                "missing_skills",
                [],
            )

            strengths = llm_result.get(
                "strengths",
                [],
            )

            justification = llm_result.get(
                "justification",
                "",
            )

        # --------------------------------------------------
        # 2. Fallback to deterministic matcher
        # --------------------------------------------------

        except Exception as exc:

            print(
                "\n===== LLM SCREENING FALLBACK ====="
            )
            print(
                f"{type(exc).__name__}: {exc}"
            )
            print(
                "Using deterministic matcher."
            )
            print(
                "==================================\n"
            )

            match_result = match_resume_to_job(
                resume,
                job_description,
            )

            # The deterministic matcher uses a score
            # from 0-100, while screening uses 0-10.
            raw_score = float(
                getattr(
                    match_result,
                    "score",
                    0,
                )
            )

            if raw_score > 10:
                score = raw_score / 10
            else:
                score = raw_score

            recommendation = getattr(
                match_result,
                "recommendation",
                None,
            )

            matched_skills = getattr(
                match_result,
                "matched_skills",
                [],
            )

            missing_skills = getattr(
                match_result,
                "missing_skills",
                [],
            )

            strengths = getattr(
                match_result,
                "strengths",
                [],
            )

            justification = getattr(
                match_result,
                "justification",
                "",
            )

        # --------------------------------------------------
        # 3. Normalize values
        # --------------------------------------------------

        if matched_skills is None:
            matched_skills = []

        if missing_skills is None:
            missing_skills = []

        if strengths is None:
            strengths = []

        if justification is None:
            justification = ""

        # --------------------------------------------------
        # 4. Build screening result
        # --------------------------------------------------

        results.append(
            {
                "candidate_name": resume.name,
                "resume_filename": filename,
                "score": score,
                "classification": classify_score(
                    score
                ),
                "recommendation": recommendation,
                "matched_skills": matched_skills,
                "missing_skills": missing_skills,
                "strengths": strengths,
                "justification": justification,
            }
        )

    # --------------------------------------------------
    # 5. Highest score first
    # --------------------------------------------------

    results.sort(
        key=lambda item: item["score"],
        reverse=True,
    )

    # --------------------------------------------------
    # 6. Add ranking
    # --------------------------------------------------

    for index, result in enumerate(
        results,
        start=1,
    ):
        result["rank"] = index

    return results