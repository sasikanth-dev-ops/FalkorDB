from pydantic import BaseModel, Field


class PrerequisitePath(BaseModel):
    known_skill: str
    target_skill: str
    path: list[str] = Field(min_length=2)


class OpportunityRead(BaseModel):
    id: str
    title: str
    type: str
    platform: str
    deadline: str | None = None
    url: str
    category: str | None = None
    description: str | None = None
    required_skills: list[str] = Field(default_factory=list)
    matched_skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    match_percentage: float | None = None
    similarity_score: float | None = None
    hybrid_score: float | None = None
    prerequisite_paths: list[PrerequisitePath] = Field(default_factory=list)
