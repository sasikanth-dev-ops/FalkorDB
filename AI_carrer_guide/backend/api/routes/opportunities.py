import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from requests import RequestException

from backend.api.dependencies import get_graph_dependency, run_graph_operation
from backend.config.env import get_settings
from backend.database import write_ops
from backend.database.hybrid_retriever import hybrid_search_opportunities
from backend.database.read_ops import GraphClient, list_opportunities
from backend.models.ingestion import ScrapeRequest, ScrapeResponse, SourceIngestionResult
from backend.models.opportunity import OpportunityRead
from scrapers.service import configured_sources, scrape_configured_sources

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/opportunities", tags=["opportunities"])


@router.get("", response_model=list[OpportunityRead])
def get_opportunities(
    student_id: str | None = None,
    query: str | None = Query(default=None, max_length=200),
    event_type: str | None = Query(default=None, alias="type", max_length=50),
    category: str | None = Query(default=None, max_length=100),
    limit: int = Query(default=20, ge=1, le=100),
    include_demo: bool = False,
    graph: GraphClient = Depends(get_graph_dependency),
) -> list[OpportunityRead]:
    if student_id is not None:
        student = run_graph_operation(
            lambda: graph.query(
                "MATCH (student:Student {id: $student_id}) RETURN student.id",
                {"student_id": student_id},
            )
        )
        if not student.result_set:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student not found",
            )
    opportunities = run_graph_operation(
        lambda: hybrid_search_opportunities(
            graph,
            student_id=student_id,
            query=query,
            event_type=event_type,
            category=category,
            limit=limit,
            include_demo=include_demo,
        )
    )
    return [OpportunityRead.model_validate(item) for item in opportunities]


@router.post("/scrape", response_model=ScrapeResponse)
def scrape_opportunities(
    request: ScrapeRequest,
    graph: GraphClient = Depends(get_graph_dependency),
) -> ScrapeResponse:
    try:
        sources = configured_sources(get_settings(), request.sources)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    try:
        scraped = scrape_configured_sources(sources)
    except (RequestException, ValueError) as exc:
        logger.exception("Configured opportunity source scrape failed")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Opportunity source could not be scraped: {exc}",
        ) from exc

    all_opportunities = [
        opportunity
        for _, opportunities in scraped
        for opportunity in opportunities
    ]
    ingested = run_graph_operation(
        lambda: write_ops.upsert_opportunities(
            graph,
            [opportunity.graph_record() for opportunity in all_opportunities],
        )
    )
    return ScrapeResponse(
        ingested=ingested,
        sources=[
            SourceIngestionResult(source=source, records=len(opportunities))
            for source, opportunities in scraped
        ],
    )
