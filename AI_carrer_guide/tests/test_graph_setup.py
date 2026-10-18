import unittest
from types import SimpleNamespace

from backend.database import setup
from backend.database.seed_data import EVENTS, SKILLS, STUDENTS


class FakeGraph:
    def __init__(self) -> None:
        self.indexes: list[list[object]] = []
        self.created_indexes: list[tuple[str, tuple[str, ...]]] = []
        self.queries: list[tuple[str, dict[str, object] | None]] = []

    def list_indices(self) -> SimpleNamespace:
        return SimpleNamespace(result_set=self.indexes)

    def create_node_range_index(self, label: str, *properties: str) -> None:
        self.created_indexes.append((label, properties))
        self.indexes.append(
            [label, list(properties), {prop: ["RANGE"] for prop in properties},
             None, None, None, "NODE"]
        )

    def query(
        self, query: str, params: dict[str, object] | None = None
    ) -> SimpleNamespace:
        self.queries.append((query, params))
        if query in setup.COUNT_QUERIES.values():
            entity = next(
                name for name, count_query in setup.COUNT_QUERIES.items()
                if count_query == query
            )
            count = {
                "students": len(STUDENTS),
                "skills": len(SKILLS),
                "events": len(EVENTS),
                "courses": len(setup.COURSES),
            }[entity]
            return SimpleNamespace(result_set=[[count]])
        return SimpleNamespace(result_set=[])


class GraphSetupTests(unittest.TestCase):
    def test_bootstrap_creates_indexes_and_loads_expected_counts(self) -> None:
        graph = FakeGraph()

        counts = setup.bootstrap_graph(graph)

        self.assertEqual(
            counts,
            {
                "students": 5,
                "skills": 20,
                "events": 10,
                "courses": 10,
            },
        )
        self.assertEqual(len(graph.created_indexes), len(setup.RANGE_INDEXES))
        self.assertEqual(len(graph.queries), len(setup.COUNT_QUERIES) + 9)

    def test_bootstrap_skips_existing_range_indexes(self) -> None:
        graph = FakeGraph()
        setup.ensure_range_indexes(graph)
        created_once = list(graph.created_indexes)

        setup.ensure_range_indexes(graph)

        self.assertEqual(graph.created_indexes, created_once)


if __name__ == "__main__":
    unittest.main()
