import json
from enum import StrEnum
from typing import Protocol

from google import genai
from google.genai import types
from pydantic import BaseModel, Field


class ChatIntent(StrEnum):
    general = "general"
    opportunities = "opportunities"
    roadmap = "roadmap"


class ExtractedSkill(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    category: str | None = Field(default=None, max_length=100)
    proficiency: str | None = Field(
        default=None, pattern="^(beginner|intermediate|advanced)$"
    )


class ExtractedGoal(BaseModel):
    description: str = Field(min_length=1, max_length=500)
    target_date: str | None = Field(default=None, pattern=r"^\d{4}-\d{2}-\d{2}$")


class ExtractedProject(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    repo_url: str | None = None
    tech_stack: list[str] = Field(default_factory=list)
    description: str | None = Field(default=None, max_length=1000)


class MemoryExtraction(BaseModel):
    intent: ChatIntent = ChatIntent.general
    skills: list[ExtractedSkill] = Field(default_factory=list)
    goals: list[ExtractedGoal] = Field(default_factory=list)
    projects: list[ExtractedProject] = Field(default_factory=list)


class ModelOutputError(RuntimeError):
    """Raised when the model provider returns unusable structured output."""


class ModelClient(Protocol):
    class Models(Protocol):
        def generate_content(
            self,
            *,
            model: str,
            contents: str,
            config: types.GenerateContentConfig,
        ) -> object: ...

    models: Models


class GeminiMemoryExtractor:
    def __init__(self, client: ModelClient, model: str) -> None:
        self._client = client
        self._model = model

    def extract(self, message: str, profile: dict[str, object]) -> MemoryExtraction:
        prompt = f"""
You extract explicit, durable facts from a student's message for their career profile.
Only capture facts the student states about themselves. Do not turn questions, examples,
hypotheticals, or assistant suggestions into student facts. Do not infer proficiency.
If the student explicitly says they are learning a skill, use beginner unless they state
a higher level. Otherwise leave proficiency unset unless they state it.
Use intent=opportunities when they ask to find or compare opportunities, intent=roadmap
when they ask how to learn or prepare, otherwise use general.
Return only facts newly stated or corrected in this message; use empty lists otherwise.
Normalize skill names but do not invent technologies. Include projects only when a project
is explicitly described. Goals should represent an explicit objective or target role.

Existing profile for context only (not new facts):
{json.dumps(profile, ensure_ascii=False)}

Student message:
{message}
"""
        models_to_try = [self._model]
        last_error = None

        for candidate_model in models_to_try:
            try:
                response = self._client.models.generate_content(
                    model=candidate_model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=MemoryExtraction,
                        temperature=0.1,
                        max_output_tokens=512,
                        thinking_config=types.ThinkingConfig(thinking_budget=0),
                    ),
                )
                response_text = getattr(response, "text", None)
                if not isinstance(response_text, str) or not response_text.strip():
                    continue
                return MemoryExtraction.model_validate_json(response_text)
            except Exception as exc:
                last_error = exc
                continue

        raise ModelOutputError(f"Gemini memory extraction failed across models: {last_error}") from last_error


class GeminiReplyGenerator:
    def __init__(self, client: ModelClient, model: str) -> None:
        self._client = client
        self._model = model

    def generate(
        self,
        *,
        message: str,
        profile: dict[str, object],
        opportunities: list[dict[str, object]],
        roadmap: list[dict[str, object]],
    ) -> str:
        prompt = f"""
You are AI Career Mentor, a practical and encouraging career co-pilot.
Answer the student's latest message. Use only the profile, opportunity records, and roadmap
provided below for factual claims. Never invent listings, eligibility, deadlines, or resources.
If a list is empty, say the relevant data is not available yet. Keep the answer under 80 words.
Return only the required JSON object; do not include analysis, preambles, or extra fields.
Explain opportunity fit from matched and missing skills when records are supplied. Treat
prerequisite_paths as graph-supported learning routes only: never claim the student owns a
target skill just because a prerequisite path reaches it. Use the supplied roadmap order.

Student message:
{message}

Known student profile:
{json.dumps(profile, ensure_ascii=False)}

Verified opportunity records:
{json.dumps(opportunities, ensure_ascii=False)}

Roadmap steps:
{json.dumps(roadmap, ensure_ascii=False)}
"""
        models_to_try = [self._model]
        last_error = None

        for candidate_model in models_to_try:
            try:
                response = self._client.models.generate_content(
                    model=candidate_model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=ReplyOutput,
                        temperature=0.3,
                        max_output_tokens=1024,
                        thinking_config=types.ThinkingConfig(thinking_budget=0),
                    ),
                )
                response_text = getattr(response, "text", None)
                if not isinstance(response_text, str) or not response_text.strip():
                    continue
                return ReplyOutput.model_validate_json(response_text).answer
            except Exception as exc:
                last_error = exc
                continue

        raise ModelOutputError(f"Gemini reply generation failed across models: {last_error}") from last_error


class ReplyOutput(BaseModel):
    answer: str = Field(min_length=1, max_length=1200)


def create_gemini_client(api_key: str) -> genai.Client:
    return genai.Client(
        api_key=api_key,
        http_options=types.HttpOptions(
            timeout=10_000,
            retry_options=types.HttpRetryOptions(attempts=1),
        ),
    )
