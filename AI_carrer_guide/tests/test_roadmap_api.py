import unittest
from types import SimpleNamespace
from typing import Any

from fastapi.testclient import TestClient

from backend.api.dependencies import get_graph_dependency
from backend.main import app


class FakeGraph:
    def __init__(self, *, student_exists: bool = True, with_opportunity: bool = True) -> None:
        self.student_exists = student_exists
        self.with_opportunity = with_opportunity
        self.calls: list[tuple[str, dict[str, Any] | None]] = []

    def query(
        self, query: str, params: dict[str, Any] | None = None
    ) -> SimpleNamespace:
        self.calls.append((query, params))
        if "PREREQUISITE_FOR" in query:
            rows = []
        elif "RETURN student.id" in query:
            rows = [["student-1"]] if self.student_exists else []
        elif "MATCH (event:Event)" in query:
            rows = (
                [[
                    "event-1",
                    "AI Buildathon",
                    "Hackathon",
                    "Community",
                    "2099-08-01",
                    "https://example.org/event-1",
                    "AI",
                    "Build an AI application.",
                    ["Python", "Vector Search"],
                    ["Python"],
                ]]
                if self.with_opportunity
                else []
            )
        elif "UNWIND $skills" in query:
            rows = [["Vector Search", "Vector Databases 101", "Example", 3, "https://example.org/course"]]
        else:
            rows = []
        return SimpleNamespace(result_set=rows)


class RoadmapApiTests(unittest.TestCase):
    def tearDown(self) -> None:
        app.dependency_overrides.clear()

    def test_roadmap_returns_steps_for_top_ranked_opportunity(self) -> None:
        graph = FakeGraph()
        app.dependency_overrides[get_graph_dependency] = lambda: graph

        response = TestClient(app).get(
            "/api/v1/roadmap", params={"student_id": "student-1"}
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            [{
                "step": 1,
                "skill": "Vector Search",
                "action": "Build foundational knowledge in Vector Search",
                "resource": {
                    "skill": "Vector Search",
                    "title": "Vector Databases 101",
                    "provider": "Example",
                    "duration_hours": 3,
                    "url": "https://example.org/course",
                },
                "target_opportunity_id": "event-1",
            }],
        )

    def test_roadmap_returns_not_found_for_unknown_student(self) -> None:
        graph = FakeGraph(student_exists=False)
        app.dependency_overrides[get_graph_dependency] = lambda: graph

        response = TestClient(app).get(
            "/api/v1/roadmap", params={"student_id": "missing"}
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["detail"], "Student not found")
        self.assertEqual(len(graph.calls), 1)

    def test_roadmap_is_empty_when_no_opportunities_are_available(self) -> None:
        graph = FakeGraph(with_opportunity=False)
        app.dependency_overrides[get_graph_dependency] = lambda: graph

        response = TestClient(app).get(
            "/api/v1/roadmap", params={"student_id": "student-1"}
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])


if __name__ == "__main__":
    unittest.main()