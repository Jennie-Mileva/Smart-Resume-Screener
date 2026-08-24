from typing import List

from pydantic import BaseModel, Field


class SkillMatchResult(BaseModel):
    matched_required_skills: List[str] = Field(default_factory=list)
    missing_required_skills: List[str] = Field(default_factory=list)

    matched_preferred_skills: List[str] = Field(default_factory=list)
    missing_preferred_skills: List[str] = Field(default_factory=list)

    required_match_percentage: float = 0.0
    preferred_match_percentage: float = 0.0


class ExperienceMatchResult(BaseModel):
    matched: bool = False
    match_percentage: float = 0.0
    details: List[str] = Field(default_factory=list)


class EducationMatchResult(BaseModel):
    matched: bool = False
    match_percentage: float = 0.0
    details: List[str] = Field(default_factory=list)


class ProjectMatchResult(BaseModel):
    matched_projects: List[str] = Field(default_factory=list)
    match_percentage: float = 0.0
    details: List[str] = Field(default_factory=list)


class MatchResult(BaseModel):
    candidate_name: str | None = None

    skill_match: SkillMatchResult
    experience_match: ExperienceMatchResult = Field(
        default_factory=ExperienceMatchResult
    )
    education_match: EducationMatchResult = Field(
        default_factory=EducationMatchResult
    )
    project_match: ProjectMatchResult = Field(
        default_factory=ProjectMatchResult
    )

    overall_score: float = 0.0