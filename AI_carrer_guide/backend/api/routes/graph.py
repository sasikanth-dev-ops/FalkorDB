from fastapi import APIRouter, Depends, HTTPException, status

from backend.api.dependencies import get_graph_dependency, run_graph_operation
from backend.database.read_ops import GraphClient, get_student_graph
from backend.models.graph import GraphState

router = APIRouter(prefix="/graph", tags=["graph"])


@router.get("/state/{student_id}", response_model=GraphState)
def get_graph_state(
    student_id: str,
    graph: GraphClient = Depends(get_graph_dependency),
) -> GraphState:
    state = run_graph_operation(lambda: get_student_graph(graph, student_id))
    if state is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    return GraphState.model_validate(state)
