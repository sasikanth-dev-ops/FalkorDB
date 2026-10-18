import unittest
from types import SimpleNamespace
from typing import Any

from backend.database.write_ops import upsert_opportunities


class FakeGraph:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, Any] | None]] = []

    def query(
        self, query: str, params: dict[str, Any] | None = None
    ) -> SimpleNamespace:
        self.calls.append((query, params))
        return SimpleNamespace(result_set=[])


class OpportunityIngestionTests(unittest.TestCase):
    def test_empty_batch_does_not_run_a_query(self) -> None:
        graph = FakeGraph()

        result = upsert_opportunities(graph, [])

        self.assertEqual(result, 0)
        self.assertEqual(graph.calls, [])

    def test_batch_uses_normalized_event_records_and_skill_requirements(self) -> None:
        graph = FakeGraph()
        opportunity = {
            "id": "opp-1",
            "title": "AI Hackathon",
            "type": "Hackathon",
            "platform": "Unstop",
            "deadline": "2026-12-01",
            "url": "https://unstop.com/events/ai-hackathon",
            "category": "AI",
            "description": "Build an AI tool.",
            "required_skills": ["Python", "Vector Search"],
        }

        result = upsert_opportunities(graph, [opportunity])

        self.assertEqual(result, 1)
        self.assertEqual(len(graph.calls), 2)
        event_query, event_params = graph.calls[0]
        query, params = graph.calls[1]
        self.assertIn("MERGE (event:Event {id: row.id})", event_query)
        self.assertEqual(event_params, {"opportunities": [opportunity]})
        self.assertIn("MATCH (event:Event {id: row.id})", query)
        self.assertIn("MERGE (event)-[:REQUIRES_SKILL]->(skill)", query)
        self.assertEqual(params, {"opportunities": [opportunity]})
        self.assertIn("DELETE relationship", query)


if __name__ == "__main__":
    unittest.main()
