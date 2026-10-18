import unittest
from datetime import date, timedelta
from types import SimpleNamespace
from typing import Any

from backend.agents.roadmap_generator import generate_roadmap
from backend.database.in_memory_graph import InMemoryGraph
from backend.database.read_ops import (
    get_student_graph,
    list_opportunities,
)
from backend.database.write_ops import upsert_opportunities


class FakeGraph:
    def __init__(self, result_sets: list[list[list[Any]]]) -> None:
        self.result_sets = iter(result_sets)
        self.calls: list[tuple[str, dict[str, Any] | None]] = []

    def query(
        self, query: str, params: dict[str, Any] | None = None
    ) -> SimpleNamespace:
        self.calls.append((query, params))
        return SimpleNamespace(result_set=next(self.result_sets))


class ApiReadTests(unittest.TestCase):
    def test_synthetic_seed_opportunities_are_hidden_by_default(self) -> None:
        graph = InMemoryGraph()

        self.assertEqual(
            list_opportunities(graph, student_id="seed-student-001"),
            [],
        )
        self.assertEqual(
            len(list_opportunities(graph, student_id="seed-student-001", include_demo=True)),
            len(graph._events),
        )

    def test_expired_opportunities_are_not_recommended(self) -> None:
        graph = InMemoryGraph()
        upsert_opportunities(
            graph,
            [
                {
                    "id": "expired-live-event",
                    "title": "Expired listing",
                    "type": "Hackathon",
                    "platform": "WeMakeDevs",
                    "deadline": (date.today() - timedelta(days=1)).isoformat(),
                    "url": "https://www.wemakedevs.org/hackathons/expired",
                    "required_skills": [],
                },
                {
                    "id": "current-live-event",
                    "title": "Current listing",
                    "type": "Hackathon",
                    "platform": "WeMakeDevs",
                    "deadline": (date.today() + timedelta(days=1)).isoformat(),
                    "url": "https://www.wemakedevs.org/hackathons/current",
                    "required_skills": [],
                },
            ],
        )

        results = list_opportunities(graph, event_type="Hackathon")

        self.assertEqual([item["title"] for item in results], ["Current listing"])
        self.assertIsNone(results[0]["match_percentage"])

    def test_in_memory_graph_exposes_prerequisite_paths_for_the_roadmap(self) -> None:
        opportunities = list_opportunities(
            InMemoryGraph(),
            student_id="seed-student-001",
            limit=100,
            include_demo=True,
        )
        target = next(
            opportunity
            for opportunity in opportunities
            if opportunity["id"] == "seed-event-001"
        )

        self.assertEqual(
            target["prerequisite_paths"],
            [{
                "known_skill": "Python",
                "target_skill": "Generative AI",
                "path": ["Python", "Machine Learning", "Generative AI"],
            }],
        )
        roadmap = generate_roadmap(InMemoryGraph(), [target])
        self.assertEqual(
            [step["skill"] for step in roadmap],
            ["Machine Learning", "Generative AI", "Vector Search"],
        )

    def test_ml_profile_roadmap_follows_live_graph_prerequisite(self) -> None:
        graph = InMemoryGraph()
        opportunities = list_opportunities(
            graph, student_id="seed-student-005", limit=100, include_demo=True
        )
        target = next(
            opportunity
            for opportunity in opportunities
            if opportunity["id"] == "seed-event-006"
        )

        roadmap = generate_roadmap(graph, [target])

        self.assertEqual(
            target["prerequisite_paths"][0]["path"],
            ["Python", "Machine Learning"],
        )
        self.assertEqual(roadmap[0]["skill"], "Machine Learning")
        self.assertEqual(
            roadmap[0]["resource"]["title"],
            "Machine Learning Specialization",
        )

    def test_opportunity_match_returns_score_and_missing_skills(self) -> None:
        graph = FakeGraph(
            [
                [[
                    "event-1",
                    "AI Buildathon",
                    "Hackathon",
                    "Community",
                    "2099-08-01",
                    "https://example.org/event-1",
                    "AI",
                    "Build an AI application.",
                    ["Python", "Vector Search", "Generative AI"],
                    ["Python"],
                ]],
                [[
                    "event-1",
                    "Python",
                    ["Python", "Machine Learning", "Generative AI"],
                ]],
            ]
        )

        results = list_opportunities(
            graph, student_id="student-1", include_demo=True
        )

        self.assertEqual(results[0]["matched_skills"], ["Python"])
        self.assertEqual(
            results[0]["missing_skills"], ["Vector Search", "Generative AI"]
        )
        self.assertEqual(
            results[0]["prerequisite_paths"],
            [{
                "known_skill": "Python",
                "target_skill": "Generative AI",
                "path": ["Python", "Machine Learning", "Generative AI"],
            }],
        )
        self.assertAlmostEqual(results[0]["match_percentage"], 100 / 3)
        self.assertEqual(graph.calls[0][1]["student_id"], "student-1")
        self.assertTrue(graph.calls[0][1]["include_demo"])
        self.assertIn("PREREQUISITE_FOR*1..3", graph.calls[1][0])

    def test_opportunity_listing_without_student_has_no_personal_match_score(self) -> None:
        graph = FakeGraph(
            [[[
                "event-1",
                "AI Buildathon",
                "Hackathon",
                "Community",
                None,
                "https://example.org/event-1",
                "AI",
                "Build an AI application.",
                ["Python"],
                [],
            ]]]
        )

        results = list_opportunities(graph, include_demo=True)

        self.assertIsNone(results[0]["match_percentage"])
        self.assertEqual(results[0]["missing_skills"], ["Python"])

    def test_student_graph_returns_student_when_no_relationships_exist(self) -> None:
        graph = FakeGraph(
            [
                [[101, ["Student"], {"id": "student-1", "name": "Ari"}]],
                [],
            ]
        )

        state = get_student_graph(graph, "student-1")

        self.assertIsNotNone(state)
        assert state is not None
        self.assertEqual(state["student_id"], "student-1")
        self.assertEqual(len(state["nodes"]), 1)
        self.assertEqual(state["edges"], [])


if __name__ == "__main__":
    unittest.main()
