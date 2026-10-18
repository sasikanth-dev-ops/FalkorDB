from enum import StrEnum

from pydantic import BaseModel, Field

from backend.models.opportunity import OpportunityRead
from backend.models.student import StudentProfile


class ChatIntentRead(StrEnum):
    general = "general"
    opportunities = "opportunities"
    roadmap = "roadmap"


class ChatRequest(BaseModel):
    student_id: str = Field(min_length=1, max_length=100)
    message: str = Field(min_length=1, max_length=4000)


class MemoryUpdates(BaseModel):
    skills: list[str] = Field(default_factory=list)
    goals: list[str] = Field(default_factory=list)
    projects: list[str] = Field(default_factory=list)


class RoadmapStep(BaseModel):
    step: int
    skill: str
    action: str
    resource: dict[str, object] | None = None
    target_opportunity_id: str


class ChatResponse(BaseModel):
    student_id: str
    message: str
    intent: ChatIntentRead
    model_degraded: bool = False
    memory_updates: MemoryUpdates
    opportunities: list[OpportunityRead] = Field(default_factory=list)
    roadmap: list[RoadmapStep] = Field(default_factory=list)
    profile: StudentProfile
