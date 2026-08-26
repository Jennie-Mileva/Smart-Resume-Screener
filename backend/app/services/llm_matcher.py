import json
import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai

from backend.app.schemas.job_description import JobDescription
from backend.app.schemas.resume import Resume


load_dotenv()


PROMPT_PATH = (
    Path(__file__).resolve().parents[2]
    / "prompts"
    / "resume_matching.txt"
)


def build_candidate_data(resume: Resume) -> dict:
    """Convert a Resume model into data suitable for the LLM."""

    return {
        "name": resume.name,
        "skills": resume.skills,
        "experience": [
            {
                "company": item.company,
                "role": item.role,
                "start_date": item.start_date,
                "end_date": item.end_date,
                "description": item.description,
            }
            for item in resume.experience
        ],
        "education": [
            {
                "degree": item.degree,
                "field_of_study": item.field_of_study,
                "institution": item.institution,
            }
            for item in resume.education
        ],
        "projects": [
            {
                "title": item.title,
                "description": item.description,
                "technologies": item.technologies,
            }
            for item in resume.projects
        ],
    }


def build_job_data(job_description: JobDescription) -> dict:
    """Convert a JobDescription model into data suitable for the LLM."""

    return {
        "title": job_description.title,
        "required_skills": job_description.required_skills,
        "preferred_skills": job_description.preferred_skills,
        "experience_requirements": (
            job_description.experience_requirements
        ),
        "education_requirements": (
            job_description.education_requirements
        ),
        "responsibilities": job_description.responsibilities,
    }


def validate_llm_result(result: dict) -> dict:
    """
    Validate and normalize the LLM matching response.

    Ensures the response contains the expected fields,
    has a valid score, and uses an allowed recommendation.
    """

    if not isinstance(result, dict):
        raise ValueError(
            "LLM response must be a JSON object"
        )

    required_fields = {
        "score",
        "recommendation",
        "matched_skills",
        "missing_skills",
        "strengths",
        "justification",
    }

    missing_fields = [
        field
        for field in required_fields
        if field not in result
    ]

    if missing_fields:
        raise ValueError(
            "LLM response is missing fields: "
            + ", ".join(missing_fields)
        )

    try:
        score = float(result["score"])
    except (TypeError, ValueError) as exc:
        raise ValueError(
            "LLM score must be a number"
        ) from exc

    if not 0 <= score <= 10:
        raise ValueError(
            "LLM score must be between 0 and 10"
        )

    allowed_recommendations = {
        "Strong Shortlist",
        "Shortlist",
        "Maybe",
        "Reject",
    }

    recommendation = result["recommendation"]

    if recommendation not in allowed_recommendations:
        raise ValueError(
            "Invalid LLM recommendation"
        )

    for field in (
        "matched_skills",
        "missing_skills",
        "strengths",
    ):
        if not isinstance(result[field], list):
            raise ValueError(
                f"LLM field '{field}' must be a list"
            )

    if not isinstance(
        result["justification"],
        str,
    ):
        raise ValueError(
            "LLM justification must be a string"
        )

    result["score"] = round(score, 2)

    return result


def load_matching_prompt(
    candidate: dict,
    job: dict,
) -> str:
    """
    Load the resume matching prompt from the external
    prompt template and insert candidate/job data.
    """

    if not PROMPT_PATH.exists():
        raise FileNotFoundError(
            f"Matching prompt not found: {PROMPT_PATH}"
        )

    template = PROMPT_PATH.read_text(
        encoding="utf-8"
    )

    return template.format(
        candidate_json=json.dumps(
            candidate,
            indent=2,
        ),
        job_json=json.dumps(
            job,
            indent=2,
        ),
    )


def parse_llm_response(text: str) -> dict:
    """
    Parse the raw LLM response into a validated dictionary.

    Handles responses wrapped in Markdown code fences.
    """

    if not text or not text.strip():
        raise ValueError(
            "LLM returned an empty response"
        )

    text = text.strip()

    if text.startswith("```"):
        lines = text.splitlines()

        if lines and lines[0].strip().lower() in {
            "```json",
            "```",
        }:
            lines = lines[1:]

        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]

        text = "\n".join(lines).strip()

    try:
        result = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(
            "LLM returned invalid JSON"
        ) from exc

    return validate_llm_result(result)


def llm_match_resume_to_job(
    resume: Resume,
    job_description: JobDescription,
) -> dict:
    """
    Evaluate a resume against a job description using Gemini.

    The prompt is loaded from backend/prompts/resume_matching.txt.
    """

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is not configured"
        )

    candidate = build_candidate_data(resume)
    job = build_job_data(job_description)

    prompt = load_matching_prompt(
        candidate,
        job,
    )

    client = genai.Client(
        api_key=api_key
    )

    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt,
    )

    return parse_llm_response(
        response.text
    )