import unittest

from backend.database.hybrid_retriever import (
    _tokenize,
    compute_cosine_similarity,
    hybrid_search_opportunities,
)


class FakeGraphClient:
    def __init__(self, opportunities_data):
        self.opportunities_data = opportunities_data

    def query(self, query: str, params=None):
        class Result:
            def __init__(self, rows):
                self.result_set = rows

        if "PREREQUISITE_FOR" in query:
            return Result([])

        # Fake Cypher result matching read_ops.list_opportunities
        rows = []
        for opp in self.opportunities_data:
            rows.append(
                [
                    opp["id"],
                    opp["title"],
                    opp["type"],
                    opp["platform"],
                    opp.get("deadline"),
                    opp["url"],
                    opp.get("category"),
                    opp.get("description"),
                    opp.get("required_skills", []),
                    opp.get("matched_skills", []),
                ]
            )
        return Result(rows)


class TestHybridRetriever(unittest.TestCase):
    def test_tokenization(self):
        tokens = _tokenize("FastAPI & Python 3.11 with Docker!")
        self.assertIn("fastapi", tokens)
        self.assertIn("python", tokens)
        self.assertIn("docker", tokens)

    def test_cosine_similarity(self):
        query = ["python", "ai", "hackathon"]
        doc1 = ["global", "ai", "hackathon", "python", "fastapi"]
        doc2 = ["frontend", "react", "css"]

        score1 = compute_cosine_similarity(query, doc1)
        score2 = compute_cosine_similarity(query, doc2)

        self.assertGreater(score1, 0.0)
        self.assertEqual(score2, 0.0)
        self.assertGreater(score1, score2)

    def test_hybrid_search(self):
        opps = [
            {
                "id": "opp-1",
                "title": "Global AI Hackathon 2026",
                "type": "Hackathon",
                "platform": "WeMakeDevs",
                "deadline": "2026-11-01",
                "url": "https://example.org/ai-hack",
                "category": "AI",
                "description": "Build agentic AI applications with Python and vector search",
                "required_skills": ["Python", "FastAPI"],
                "matched_skills": ["Python"],
            },
            {
                "id": "opp-2",
                "title": "Web3 Frontend Bounty",
                "type": "Bounty",
                "platform": "GitHub",
                "deadline": "2026-12-01",
                "url": "https://example.org/web3-bounty",
                "category": "Web3",
                "description": "Solidity smart contract and React UI bounty",
                "required_skills": ["Solidity", "React"],
                "matched_skills": [],
            },
        ]

        graph = FakeGraphClient(opps)
        results = hybrid_search_opportunities(
            graph,
            student_id="student-1",
            query="AI agentic Python",
            limit=5,
            include_demo=True,
        )

        self.assertEqual(len(results), 2)
        top = results[0]
        self.assertEqual(top["id"], "opp-1")
        self.assertIsNotNone(top.get("similarity_score"))
        self.assertIsNotNone(top.get("hybrid_score"))
        self.assertGreater(top["similarity_score"], 0.0)
        self.assertGreater(top["hybrid_score"], 0.0)


if __name__ == "__main__":
    unittest.main()
