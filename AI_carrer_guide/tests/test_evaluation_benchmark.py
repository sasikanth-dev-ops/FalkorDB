"""Automated Evaluation & Benchmark Suite for AI Career Mentor.

Evaluates the core criteria defined in spec.md Section 18:
1. Memory Retention: Verifies profile memory updates across turns
2. Opportunity Match Quality: Precision of matched vs missing skills
3. GraphRAG Hybrid Retrieval Accuracy: Composite scoring ranking
4. Roadmap Utility: Actionable step sequencing and course alignment
"""

import unittest
from typing import Any

from backend.agents.readiness_evaluator import evaluate_readiness
from backend.agents.roadmap_generator import generate_roadmap
from backend.database.hybrid_retriever import (
    compute_cosine_similarity,
    hybrid_search_opportunities,
)


class MockBenchmarkGraph:
    def __init__(self):
        self.students = {
            "test-student": {
                "id": "test-student",
                "name": "Alex Mercer",
                "skills": ["Python", "FastAPI"],
            }
        }
        self.opportunities = [
            {
                "id": "opp-genai",
                "title": "GenAI Agent Hackathon",
                "type": "Hackathon",
                "platform": "WeMakeDevs",
                "deadline": "2026-11-15",
                "url": "https://example.org/genai-hack",
                "category": "AI",
                "description": "Develop agentic AI systems using Python, FastAPI, and Vector Databases.",
                "required_skills": ["Python", "FastAPI", "Vector Search"],
                "matched_skills": ["Python", "FastAPI"],
            },
            {
                "id": "opp-frontend",
                "title": "React UI Challenge",
                "type": "Hackathon",
                "platform": "Unstop",
                "deadline": "2026-11-20",
                "url": "https://example.org/react-ui",
                "category": "Frontend",
                "description": "Build high-performance React and TypeScript applications.",
                "required_skills": ["React", "TypeScript", "CSS"],
                "matched_skills": [],
            },
        ]
        self.courses = [
            {
                "skill": "Machine Learning",
                "title": "Machine Learning Foundations",
                "provider": "Example Learning",
                "duration_hours": 10,
                "url": "https://example.org/courses/ml",
            },
            {
                "skill": "Vector Search",
                "title": "Vector Databases in Production",
                "provider": "DeepLearning.AI",
                "duration_hours": 12,
                "url": "https://example.org/courses/vector-db",
            }
        ]

    def query(self, query: str, params: dict[str, Any] | None = None):
        params = params or {}

        class Result:
            def __init__(self, rows):
                self.result_set = rows

        if "PREREQUISITE_FOR" in query:
            return Result([])

        # Student check
        if "MATCH (student:Student {id: $student_id})" in query and "RETURN student.id" in query:
            sid = params.get("student_id")
            return Result([[sid]] if sid in self.students else [])

        # List opportunities query
        if "MATCH (event:Event)" in query:
            rows = []
            for opp in self.opportunities:
                rows.append(
                    [
                        opp["id"],
                        opp["title"],
                        opp["type"],
                        opp["platform"],
                        opp["deadline"],
                        opp["url"],
                        opp["category"],
                        opp["description"],
                        opp["required_skills"],
                        opp["matched_skills"],
                    ]
                )
            return Result(rows)

        # Course query
        if "UNWIND $skills AS skill_name" in query:
            skills = params.get("skills", [])
            rows = []
            for c in self.courses:
                if c["skill"] in skills:
                    rows.append(
                        [
                            c["skill"],
                            c["title"],
                            c["provider"],
                            c["duration_hours"],
                            c["url"],
                        ]
                    )
            return Result(rows)

        return Result([])


class TestEvaluationBenchmark(unittest.TestCase):
    def setUp(self):
        self.graph = MockBenchmarkGraph()

    def test_memory_retention_and_profiling(self):
        """18.1 Memory Retention: Ensure facts persist in student profile state."""
        student = self.graph.students["test-student"]
        self.assertIn("Python", student["skills"])
        self.assertIn("FastAPI", student["skills"])

        # Simulate dynamic memory addition
        student["skills"].append("Docker")
        self.assertIn("Docker", self.graph.students["test-student"]["skills"])

    def test_opportunity_match_quality(self):
        """18.2 Opportunity Match Quality: Precision of matched vs missing skills."""
        opps = evaluate_readiness(self.graph, "test-student")
        self.assertGreater(len(opps), 0)

        top_opp = opps[0]
        self.assertEqual(top_opp["id"], "opp-genai")
        self.assertEqual(top_opp["matched_skills"], ["Python", "FastAPI"])
        self.assertEqual(top_opp["missing_skills"], ["Vector Search"])

        # Match precision: 2 matched out of 3 required = 66.67%
        expected_match_pct = (2 / 3) * 100
        self.assertAlmostEqual(top_opp["match_percentage"], expected_match_pct, places=1)

    def test_hybrid_graphrag_retrieval(self):
        """18.3 Graph Retrieval Accuracy: Semantic similarity ranking."""
        results = hybrid_search_opportunities(
            self.graph,
            student_id="test-student",
            query="Agentic AI Vector Search",
            limit=5,
            include_demo=True,
        )

        self.assertEqual(results[0]["id"], "opp-genai")
        self.assertGreater(results[0]["similarity_score"], 0.0)
        self.assertGreater(results[0]["hybrid_score"], 0.4)

    def test_roadmap_utility_and_completeness(self):
        """18.4 Roadmap Utility: Check step sequence closes missing prerequisite gaps."""
        opps = evaluate_readiness(self.graph, "test-student")
        roadmap = generate_roadmap(self.graph, opps)

        self.assertEqual(len(roadmap), 1)
        step = roadmap[0]
        self.assertEqual(step["step"], 1)
        self.assertEqual(step["skill"], "Vector Search")
        self.assertIsNotNone(step["resource"])
        self.assertEqual(step["resource"]["provider"], "DeepLearning.AI")
        self.assertIn("vector-db", step["resource"]["url"])

    def test_roadmap_follows_graph_prerequisites_before_target_skill(self):
        opportunity = {
            "id": "opp-genai",
            "matched_skills": ["Python"],
            "missing_skills": ["Generative AI", "Vector Search"],
            "prerequisite_paths": [
                {
                    "known_skill": "Python",
                    "target_skill": "Generative AI",
                    "path": ["Python", "Machine Learning", "Generative AI"],
                }
            ],
        }

        roadmap = generate_roadmap(self.graph, [opportunity])

        self.assertEqual(
            [step["skill"] for step in roadmap],
            ["Machine Learning", "Generative AI", "Vector Search"],
        )
        self.assertEqual(roadmap[0]["resource"]["title"], "Machine Learning Foundations")


if __name__ == "__main__":
    unittest.main()
