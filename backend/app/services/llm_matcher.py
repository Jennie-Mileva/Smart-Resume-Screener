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

Calculate four separate category scores from 0 to 10.

1. SKILLS — 40%
Compare the candidate's skills with the required and preferred skills.
Required skills are more important than preferred skills.

2. EXPERIENCE — 30%
Compare the candidate's actual experience with the job's experience requirements.
Do not assume experience that is not explicitly present.

3. EDUCATION — 15%
Compare the candidate's education with the stated education requirements.
Do not assume qualifications that are not provided.

4. RESPONSIBILITIES / DOMAIN ALIGNMENT — 15%
Compare the candidate's experience and projects with the responsibilities
and technical domain of the job.
Only use evidence present in the supplied candidate data.

Calculate the final score using:

final_score =
    (skills_score * 0.40) +
    (experience_score * 0.30) +
    (education_score * 0.15) +
    (responsibilities_score * 0.15)

The final score must be between 0 and 10.

Score guidance:

0-3:
Very poor match. Major required qualifications are missing.

4-5:
Some relevant qualifications, but significant gaps exist.

6-7:
Good match. A substantial portion of the important requirements is satisfied.

8-9:
Strong match. Most important requirements are satisfied with relevant evidence.

10:
Exceptional match. Essentially all important requirements are satisfied.

IMPORTANT:
- Do not invent qualifications, skills, experience, education, projects, or responsibilities.
- Base every conclusion only on the supplied candidate and job data.
- Required skills must not be treated as equivalent to preferred skills.
- Missing information must not be treated as evidence that the candidate has the qualification.


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