from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status

from backend.api.dependencies import get_graph_dependency, run_graph_operation
from backend.database import read_ops, write_ops
from backend.database.read_ops import GraphClient
from backend.models.student import StudentProfile, StudentProfileUpdate

router = APIRouter(prefix="/student", tags=["students"])


@router.get("/{student_id}", response_model=StudentProfile)
def get_student(
    student_id: str,
    graph: GraphClient = Depends(get_graph_dependency),
) -> StudentProfile:
    profile = run_graph_operation(
        lambda: read_ops.get_student_profile(graph, student_id)
    )
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    return StudentProfile.model_validate(profile)


@router.post("/profile", response_model=StudentProfile, status_code=status.HTTP_200_OK)
def save_student(
    request: StudentProfileUpdate,
    graph: GraphClient = Depends(get_graph_dependency),
) -> StudentProfile:
    profile_data = request.model_dump()
    for goal in profile_data["goals"]:
        if goal["goal_id"] is None:
            goal["goal_id"] = str(uuid4())
    run_graph_operation(lambda: write_ops.save_student_profile(graph, profile_data))
    profile = run_graph_operation(
        lambda: read_ops.get_student_profile(graph, request.student_id)
    )
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Student profile was saved but could not be retrieved",
        )
    return StudentProfile.model_validate(profile)
