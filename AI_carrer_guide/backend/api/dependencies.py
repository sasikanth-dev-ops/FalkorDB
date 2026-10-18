import logging
from collections.abc import Callable
from functools import lru_cache
from typing import TypeVar

from fastapi import HTTPException
from google import genai
from redis.exceptions import RedisError

from backend.agents.memory_extractor import create_gemini_client
from backend.agents.orchestrator import ChatOrchestrator
from backend.config.db import get_graph
from backend.config.env import get_settings
from backend.database.read_ops import GraphClient

logger = logging.getLogger(__name__)
T = TypeVar("T")


def get_graph_dependency() -> GraphClient:
    try:
        return get_graph()
    except RedisError as exc:
        logger.exception("Unable to connect to FalkorDB")
        raise HTTPException(
            status_code=503,
            detail="Graph database is unavailable",
        ) from exc


def run_graph_operation(operation: Callable[[], T]) -> T:
    try:
        return operation()
    except RedisError as exc:
        logger.exception("FalkorDB operation failed")
        raise HTTPException(
            status_code=503,
            detail="Graph database operation failed",
        ) from exc


def api_prefix() -> str:
    return get_settings().api_v1_prefix.rstrip("/")


@lru_cache(maxsize=4)
def _model_client(api_key: str) -> genai.Client:
    return create_gemini_client(api_key)


def get_chat_orchestrator() -> ChatOrchestrator:
    settings = get_settings()
    if not settings.gemini_api_key:
        raise HTTPException(
            status_code=503,
            detail="Gemini is not configured; set GEMINI_API_KEY to enable chat",
        )
    return ChatOrchestrator(
        get_graph_dependency(),
        _model_client(settings.gemini_api_key),
        settings.gemini_model,
    )
