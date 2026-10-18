from typing import Any, TypedDict

from backend.agents.memory_extractor import MemoryExtraction


class ChatState(TypedDict, total=False):
    student_id: str
    message: str
    profile: dict[str, Any]
    extraction: MemoryExtraction
    opportunities: list[dict[str, Any]]
    roadmap: list[dict[str, Any]]
    response: str
    updated_profile: dict[str, Any]
    model_degraded: bool
