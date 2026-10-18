import logging

from fastapi import APIRouter, Depends, HTTPException, status
from google.genai.errors import APIError

from backend.agents.memory_extractor import ModelOutputError
from backend.agents.orchestrator import (
    ChatOrchestrator,
    StudentProfileNotFoundError,
)
from backend.api.dependencies import get_chat_orchestrator
from backend.models.chat import ChatRequest, ChatResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/message", response_model=ChatResponse)

def chat(
    request: ChatRequest,
    orchestrator: ChatOrchestrator = Depends(get_chat_orchestrator),
) -> ChatResponse:
    try:
        result = orchestrator.invoke(request.student_id, request.message)

    except StudentProfileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                "No profile exists for this student. Create a profile or select "
                "one of the seeded demo students before chatting."
            ),
        ) from exc
    except LookupError as exc:
        logger.exception("Unexpected LookupError inside chat workflow")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected lookup error inside chat workflow. Check backend logs.",
        ) from exc

    except Exception:
        logger.exception(
            "Unexpected chat failure for student_id=%s",
            request.student_id,
        )
        raise

    return ChatResponse.model_validate(result)
