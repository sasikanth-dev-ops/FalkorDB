import json
import unittest
from types import SimpleNamespace
from typing import Any

from backend.agents.local_fallback import extract_local_intent
from backend.agents.orchestrator import ChatOrchestrator, StudentProfileNotFoundError


EXTRACTION_RESPONSE = {
    "intent": "roadmap",
    "skills": [
        {"name": "Python", "category": "Language", "proficiency": "intermediate"}
    ],
    "goals": [{"description": "Join an AI hackathon", "target_date": None}],
    "projects": [
        {
            "title": "AI Study Buddy",
            "repo_url": "https://example.org/ai-study-buddy",
            "tech_stack": ["Python"],
            "description": "A small study assistant project.",
        }
    ],
}


class FakeModelClient:
    def __init__(self, responses: list[str]) -> None:
        self.responses = iter(responses)
        self.prompts: list[str] = []

        class Models:
            def __init__(self, outer: FakeModelClient) -> None:
                self.outer = outer

            def generate_content(self, **kwargs: Any) -> SimpleNamespace:
                self.outer.prompts.append(kwargs["contents"])
                return SimpleNamespace(text=next(self.outer.responses))

        self.models = Models(self)


class FakeGraph:
    def __init__(self, student_exists: bool = True) -> None:
        self.student_exists = student_exists
        self.calls: list[tuple[str, dict[str, Any] | None]] = []

    def query(
        self, query: str, params: dict[str, Any] | None = None
    ) -> SimpleNamespace:
        self.calls.append((query, params))
        normalized_query = query.strip()
        if normalized_query.startswith("MATCH (s:Student") and "OPTIONAL MATCH" in query:
            if not self.student_exists:
                return SimpleNamespace(result_set=[])
            return SimpleNamespace(
                result_set=[
                    [
                        "student-1",
                        "Alex",
                        "Computer Science",
                        2,
                        "AI Engineer",
                        [
                            {
                                "name": "Python",
                                "category": "Language",
                                "proficiency": "intermediate",
                            }
                        ],
                        [],
                        [],
                    ]
                ]
            )
        if normalized_query.startswith("MATCH (event:Event)"):
            return SimpleNamespace(
                result_set=[
                    [
                        "event-1",
                        "AI Hackathon",
                        "Hackathon",
                        "Community",
                        "2099-08-01",
                        "https://example.org/ai-hackathon",
                        "AI",
                        "Build a useful AI project.",
                        ["Python", "Vector Search"],
                        ["Python"],
                    ]
                ]
            )
        if normalized_query.startswith("UNWIND $skills AS skill_name"):
            return SimpleNamespace(
                result_set=[
                    [
                        "Vector Search",
                        "Vector Databases 101",
                        "Example Learning",
                        6,
                        "https://example.org/vector-course",
                    ]
                ]
            )
        return SimpleNamespace(result_set=[])


class OrchestratorTests(unittest.TestCase):
    def test_local_intent_classifies_quick_demo_prompts(self) -> None:
        prompts = (
            (
                "I'm building projects with Python and FastAPI. I want to join an AI "
                "hackathon, but I'm still new to vector databases.",
                "opportunities",
            ),
            (
                "Can you recommend top opportunities for my backend skills and show "
                "me what prerequisites I am missing?",
                "opportunities",
            ),
            (
                "Please build a step-by-step roadmap to prepare me for the AI hackathon.",
                "roadmap",
            ),
        )

        for prompt, intent in prompts:
            with self.subTest(prompt=prompt):
                self.assertEqual(extract_local_intent(prompt).intent.value, intent)

    def test_chat_extracts_persists_and_uses_opportunities_for_roadmap(self) -> None:
        model = FakeModelClient(
            [
                json.dumps(EXTRACTION_RESPONSE),
                json.dumps({"answer": "Build your vector search skills next."}),
            ]
        )
        graph = FakeGraph()

        result = ChatOrchestrator(graph, model, "test-model").invoke(
            "student-1",
            "I know Python and want to join an AI hackathon. Help me prepare.",
        )

        self.assertEqual(result["intent"], "roadmap")
        self.assertEqual(result["message"], "Build your vector search skills next.")
        self.assertEqual(result["memory_updates"]["skills"], ["Python"])
        self.assertEqual(result["memory_updates"]["goals"], ["Join an AI hackathon"])
        self.assertEqual(result["memory_updates"]["projects"], ["AI Study Buddy"])
        self.assertEqual(result["opportunities"][0]["id"], "event-1")
        self.assertEqual(result["opportunities"][0]["missing_skills"], ["Vector Search"])
        self.assertEqual(result["roadmap"][0]["skill"], "Vector Search")
        self.assertEqual(result["roadmap"][0]["resource"]["title"], "Vector Databases 101")
        self.assertTrue(any("MERGE (node:Goal" in query for query, _ in graph.calls))
        self.assertTrue(any("MERGE (node:Project" in query for query, _ in graph.calls))
        self.assertEqual(len(model.prompts), 2)
        self.assertIn("prerequisite_paths as graph-supported learning routes", model.prompts[1])

    def test_chat_refuses_unknown_student_before_calling_model(self) -> None:
        model = FakeModelClient([])

        with self.assertRaises(StudentProfileNotFoundError):
            ChatOrchestrator(FakeGraph(student_exists=False), model, "test-model").invoke(
                "missing", "Hello"
            )

        self.assertEqual(model.prompts, [])

    def test_extractor_uses_local_resource_fallback_when_model_output_is_invalid(self) -> None:
        model = FakeModelClient(["not json"])

        result = ChatOrchestrator(FakeGraph(), model, "test-model").invoke(
            "student-1",
            "Hi, I want to learn MERN. Help me select a resource.",
        )

        self.assertEqual(len(model.prompts), 1)
        self.assertTrue(result["model_degraded"])
        self.assertEqual(result["intent"], "roadmap")
        self.assertIn("MongoDB", result["message"])
        self.assertIn("https://react.dev/learn", result["message"])
        self.assertEqual(result["memory_updates"], {"skills": [], "goals": [], "projects": []})


if __name__ == "__main__":
    unittest.main()
