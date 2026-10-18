import logging

logger = logging.getLogger("backend.agents.audit")


def log_chat_completed(
    *,
    student_id: str,
    intent: str,
    skill_updates: int,
    goal_updates: int,
    project_updates: int,
    opportunity_count: int,
    duration_ms: int,
) -> None:
    logger.info(
        "chat_completed student_id=%s intent=%s skill_updates=%d goal_updates=%d "
        "project_updates=%d opportunity_count=%d duration_ms=%d",
        student_id,
        intent,
        skill_updates,
        goal_updates,
        project_updates,
        opportunity_count,
        duration_ms,
    )
