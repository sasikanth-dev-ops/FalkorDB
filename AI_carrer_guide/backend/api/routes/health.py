from fastapi import APIRouter, Depends

from backend.api.dependencies import get_graph_dependency, run_graph_operation
from backend.database.read_ops import GraphClient

router = APIRouter(tags=["health"])


@router.get("/health", summary="Check API and graph database readiness")
def health(graph: GraphClient = Depends(get_graph_dependency)) -> dict[str, str]:
    def check_graph() -> None:
        graph.query("RETURN 1 AS healthy")

    run_graph_operation(check_graph)
    return {"status": "ok", "database": "ok"}
