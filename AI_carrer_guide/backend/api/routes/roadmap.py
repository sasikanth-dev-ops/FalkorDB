from fastapi import APIRouter, Depends, HTTPException, Query, status

from backend.agents.readiness_evaluator import evaluate_readiness
from backend.agents.roadmap_generator import generate_roadmap
from backend.api.dependencies import get_graph_dependency, run_graph_operation
from backend.database.read_ops import GraphClient
from backend.models.chat import RoadmapStep

router = APIRouter(prefix="/roadmap", tags=["roadmap"])


@router.get("", response_model=list[RoadmapStep])
def get_roadmap(
    student_id: str = Query(min_length=1, max_length=100),
    graph: GraphClient = Depends(get_graph_dependency),
) -> list[RoadmapStep]:
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
        lambda: evaluate_readiness(graph, student_id)
    )
    roadmap = run_graph_operation(lambda: generate_roadmap(graph, opportunities))
    return [RoadmapStep.model_validate(step) for step in roadmap]