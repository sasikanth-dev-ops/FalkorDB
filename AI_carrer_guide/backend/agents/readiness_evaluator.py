from typing import Any

from backend.database.hybrid_retriever import hybrid_search_opportunities
from backend.database.read_ops import GraphClient, list_opportunities


def evaluate_readiness(
    graph: GraphClient,
    student_id: str,
    limit: int = 5,
    *,
    query: str | None = None,
    event_type: str | None = None,
) -> list[dict[str, Any]]:
    if query or event_type:
        opportunities = hybrid_search_opportunities(
            graph,
            student_id=student_id,
            query=query,
            event_type=event_type,
            limit=max(limit, 5),
        )
    else:
        opportunities = list_opportunities(graph, student_id=student_id, limit=100)
    opportunities.sort(
        key=lambda opportunity: (
            -(opportunity.get("hybrid_score") or 0.0),
            -(opportunity["match_percentage"] or 0.0),
            len(opportunity["missing_skills"]),
            opportunity["deadline"] or "9999-12-31",
            opportunity["title"],
        )
    )
    return opportunities[:limit]
