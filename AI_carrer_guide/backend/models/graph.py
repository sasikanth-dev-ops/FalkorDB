from pydantic import BaseModel, Field


class GraphNode(BaseModel):
    id: str
    labels: list[str]
    properties: dict[str, object]


class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    type: str
    properties: dict[str, object] = Field(default_factory=dict)


class GraphState(BaseModel):
    student_id: str
    nodes: list[GraphNode]
    edges: list[GraphEdge]
