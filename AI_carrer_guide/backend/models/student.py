from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class Proficiency(StrEnum):
    beginner = "beginner"
    intermediate = "intermediate"
    advanced = "advanced"


class StudentProfileCreate(BaseModel):
    student_id: str = Field(min_length=1, max_length=100)
    name: str = Field(min_length=1, max_length=200)
    branch: str | None = Field(default=None, max_length=200)
    year: int | None = Field(default=None, ge=1, le=20)
    target_role: str | None = Field(default=None, max_length=200)


class SkillInput(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    category: str | None = Field(default=None, max_length=100)
    proficiency: Proficiency = Proficiency.beginner


class GoalInput(BaseModel):
    goal_id: str | None = Field(default=None, max_length=100)
    description: str = Field(min_length=1, max_length=500)
    target_date: str | None = Field(default=None, pattern=r"^\d{4}-\d{2}-\d{2}$")


class StudentProfileUpdate(BaseModel):
    student_id: str = Field(min_length=1, max_length=100)
    name: str = Field(min_length=1, max_length=200)
    branch: str | None = Field(default=None, max_length=200)
    year: int | None = Field(default=None, ge=1, le=20)
    target_role: str | None = Field(default=None, max_length=200)
    skills: list[SkillInput] = Field(default_factory=list, max_length=100)
    goals: list[GoalInput] = Field(default_factory=list, max_length=50)


class SkillRead(BaseModel):
    name: str
    category: str | None = None
    proficiency: str | None = None


class GoalRead(BaseModel):
    id: str
    description: str
    target_date: str | None = None


class ProjectRead(BaseModel):
    id: str
    title: str
    repo_url: str | None = None
    tech_stack: list[str] = Field(default_factory=list)


class StudentProfile(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    student_id: str
    name: str
    branch: str | None = None
    year: int | None = None
    target_role: str | None = None
    skills: list[SkillRead] = Field(default_factory=list)
    goals: list[GoalRead] = Field(default_factory=list)
    projects: list[ProjectRead] = Field(default_factory=list)
