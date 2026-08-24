from pydantic import BaseModel, Field
from typing import List, Optional


class JobDescription(BaseModel):
    title: Optional[str] = None

    required_skills: List[str] = Field(default_factory=list)
    preferred_skills: List[str] = Field(default_factory=list)

    education_requirements: List[str] = Field(default_factory=list)
    experience_requirements: List[str] = Field(default_factory=list)

    responsibilities: List[str] = Field(default_factory=list)