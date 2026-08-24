import json
import os

from dotenv import load_dotenv
from google import genai

from backend.app.schemas.job_description import JobDescription
from backend.app.schemas.resume import Resume

load_dotenv()

def build_candidate_data(resume: Resume) -> dict:
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


def llm_match_resume_to_job(
    resume: Resume,
    job_description: JobDescription,
) -> dict:
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is not configured"
        )

    client = genai.Client(api_key=api_key)

    candidate = build_candidate_data(resume)
    job = build_job_data(job_description)

    prompt = f"""
You are an expert technical recruiter.

Evaluate the candidate against the job description.

CANDIDATE:
{json.dumps(candidate, indent=2)}

JOB DESCRIPTION:
{json.dumps(job, indent=2)}

SCORING RUBRIC:

0-3:
Very poor match. Major required skills or qualifications are missing.

4-5:
Some relevant skills or experience, but significant gaps exist.

6-7:
Good match. Most important requirements are reasonably satisfied.

8-9:
Strong match. The candidate satisfies most important requirements
with relevant experience.

10:
Exceptional match. The candidate satisfies essentially all important
requirements and is highly aligned with the role.

Consider:

- Skills: 40%
- Experience: 30%
- Education: 15%
- Responsibilities/domain alignment: 15%

Do not invent qualifications, experience, skills, education, or projects.

Base every conclusion only on the supplied candidate and job data.

Return ONLY valid JSON with this exact structure:

{{
  "score": 0.0,
  "recommendation": "Shortlist",
  "matched_skills": [],
  "missing_skills": [],
  "strengths": [],
  "justification": ""
}}

The score must be between 0 and 10.

Recommendation must be one of:
"Strong Shortlist"
"Shortlist"
"Maybe"
"Reject"
"""

    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt,
    )

    text = response.text.strip()

    if text.startswith("```"):
        text = text.replace("```json", "", 1)
        text = text.replace("```", "", 1)
        text = text.strip()
    return json.loads(text)