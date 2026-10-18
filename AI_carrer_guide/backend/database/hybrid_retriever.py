"""Graph and lexical-text ranking for FalkorDB-backed opportunity search."""

from __future__ import annotations

import math
import re
from typing import Any

from backend.database.read_ops import GraphClient, list_opportunities


def _tokenize(text: str) -> list[str]:
    return [word for word in re.findall(r"\b[a-zA-Z0-9_\-\.\+]+\b", text.casefold()) if len(word) > 1]


def compute_cosine_similarity(query_tokens: list[str], doc_tokens: list[str]) -> float:
    if not query_tokens or not doc_tokens:
        return 0.0

    query_counts: dict[str, int] = {}
    for token in query_tokens:
        query_counts[token] = query_counts.get(token, 0) + 1

    doc_counts: dict[str, int] = {}
    for token in doc_tokens:
        doc_counts[token] = doc_counts.get(token, 0) + 1

    common_keys = set(query_counts.keys()).intersection(doc_counts.keys())
    if not common_keys:
        return 0.0

    dot_product = sum(query_counts[term] * doc_counts[term] for term in common_keys)
    query_norm = math.sqrt(sum(count**2 for count in query_counts.values()))
    doc_norm = math.sqrt(sum(count**2 for count in doc_counts.values()))

    if query_norm == 0.0 or doc_norm == 0.0:
        return 0.0

    return dot_product / (query_norm * doc_norm)


def hybrid_search_opportunities(
    graph: GraphClient,
    *,
    student_id: str | None = None,
    query: str | None = None,
    event_type: str | None = None,
    category: str | None = None,
    limit: int = 20,
    alpha: float = 0.55,
    include_demo: bool = False,
) -> list[dict[str, Any]]:
    """Rank opportunities using graph-derived readiness and token overlap."""
    opportunities = list_opportunities(
        graph,
        student_id=student_id,
        event_type=event_type,
        category=category,
        limit=max(limit * 3, 50),
        include_demo=include_demo,
    )

    if not opportunities:
        return []

    if not query or not query.strip():
        return opportunities[:limit]

    query_tokens = _tokenize(query)

    for item in opportunities:
        text_parts = [
            item.get("title") or "",
            item.get("description") or "",
            item.get("category") or "",
            " ".join(item.get("required_skills") or []),
            item.get("type") or "",
        ]
        doc_text = " ".join(text_parts)
        doc_tokens = _tokenize(doc_text)

        sim_score = round(compute_cosine_similarity(query_tokens, doc_tokens), 4)
        item["similarity_score"] = sim_score

        graph_pct = (item.get("match_percentage") or 0.0) / 100.0

        if student_id:
            item["hybrid_score"] = round(alpha * graph_pct + (1.0 - alpha) * sim_score, 4)
        else:
            item["hybrid_score"] = sim_score

    # Sort primarily by hybrid_score descending when query is provided
    opportunities.sort(
        key=lambda opp: (
            -(opp.get("hybrid_score") or 0.0),
            -(opp.get("match_percentage") or 0.0),
            opp.get("deadline") or "9999-12-31",
            opp.get("title") or "",
        )
    )

    return opportunities[:limit]
