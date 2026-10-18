"""Create the local graph schema and load deterministic demo data."""

from typing import Any, Protocol

from backend.config.db import get_graph
from backend.database.schema import RANGE_INDEXES
from backend.database.seed_data import (
    COURSE_SKILLS,
    COURSES,
    EVENTS,
    SKILL_PREREQUISITES,
    SKILLS,
    STUDENTS,
    STUDENT_SKILLS,
)


class QueryResult(Protocol):
    result_set: list[Any]


class GraphClient(Protocol):
    def list_indices(self) -> QueryResult: ...

    def create_node_range_index(self, label: str, *properties: str) -> Any: ...

    def query(
        self, query: str, params: dict[str, Any] | None = None
    ) -> QueryResult: ...


STUDENT_QUERY = """
UNWIND $students AS row
MERGE (s:Student {id: row.id})
SET s.name = row.name,
    s.branch = row.branch,
    s.year = row.year,
    s.target_role = row.target_role
"""

SKILL_QUERY = """
UNWIND $skills AS row
MERGE (sk:Skill {name: row.name})
SET sk.category = row.category
"""

EVENT_QUERY = """
UNWIND $events AS row
MERGE (e:Event {id: row.id})
SET e.title = row.title,
    e.type = row.type,
    e.platform = row.platform,
    e.deadline = row.deadline,
    e.url = row.url,
    e.category = row.category,
    e.description = row.description
WITH row, e
UNWIND row.skills AS skill_name
MATCH (sk:Skill {name: skill_name})
MERGE (e)-[:REQUIRES_SKILL]->(sk)
"""

COURSE_QUERY = """
UNWIND $courses AS row
MERGE (c:Course {id: row.id})
SET c.title = row.title,
    c.provider = row.provider,
    c.duration_hours = row.duration_hours,
    c.url = row.url
"""

STUDENT_SKILL_QUERY = """
UNWIND $student_skills AS row
MATCH (s:Student {id: row.student_id})
MATCH (sk:Skill {name: row.skill_name})
MERGE (s)-[r:HAS_SKILL]->(sk)
SET r.proficiency = row.proficiency
"""

STUDENT_GOAL_QUERY = """
UNWIND $students AS row
MATCH (s:Student {id: row.student_id})
MERGE (g:Goal {id: row.goal_id})
SET g.description = row.goal_description,
    g.target_date = row.target_date
MERGE (s)-[:HAS_GOAL]->(g)
"""

STUDENT_PROJECT_QUERY = """
UNWIND $students AS row
MATCH (s:Student {id: row.id})
MERGE (p:Project {id: row.project_id})
SET p.title = row.project_title,
    p.repo_url = row.project_url,
    p.tech_stack = row.tech_stack,
    p.description = row.project_description
MERGE (s)-[:BUILDING_PROJECT]->(p)
"""

COURSE_SKILL_QUERY = """
UNWIND $course_skills AS row
MATCH (c:Course {id: row.course_id})
MATCH (sk:Skill {name: row.skill_name})
MERGE (c)-[:TEACHES_SKILL]->(sk)
"""

PREREQUISITE_QUERY = """
UNWIND $prerequisites AS row
MATCH (prerequisite:Skill {name: row.prerequisite})
MATCH (skill:Skill {name: row.skill})
MERGE (prerequisite)-[:PREREQUISITE_FOR]->(skill)
"""

COUNT_QUERIES = {
    "students": "MATCH (n:Student) RETURN count(n) AS count",
    "skills": "MATCH (n:Skill) RETURN count(n) AS count",
    "events": "MATCH (n:Event) RETURN count(n) AS count",
    "courses": "MATCH (n:Course) RETURN count(n) AS count",
}


def _existing_range_indexes(graph: GraphClient) -> set[tuple[str, str]]:
    existing: set[tuple[str, str]] = set()
    for index in graph.list_indices().result_set:
        if len(index) <= 6 or index[6] != "NODE":
            continue
        label, types_by_property = index[0], index[2]
        for property_name, index_types in types_by_property.items():
            if "RANGE" in index_types:
                existing.add((label, property_name))
    return existing


def ensure_range_indexes(graph: GraphClient) -> None:
    existing = _existing_range_indexes(graph)
    for label, properties in RANGE_INDEXES.items():
        missing = [property_name for property_name in properties
                   if (label, property_name) not in existing]
        if missing:
            graph.create_node_range_index(label, *missing)


def _course_records() -> list[dict[str, Any]]:
    return [
        {
            "id": course_id,
            "title": title,
            "provider": provider,
            "duration_hours": duration_hours,
            "url": url,
        }
        for course_id, title, provider, duration_hours, url in COURSES
    ]


def _event_records() -> list[dict[str, Any]]:
    return [
        {
            "id": event["id"],
            "title": event["title"],
            "type": event["type"],
            "platform": event["platform"],
            "deadline": event["deadline"],
            "url": event["url"],
            "category": event["category"],
            "description": event["description"],
            "skills": list(event["skills"]),
        }
        for event in EVENTS
    ]


def _student_goal_records() -> list[dict[str, str]]:
    return [
        {
            "student_id": student["id"],
            "goal_id": f"seed-goal-{student['id']}",
            "goal_description": f"Prepare for a career as a {student['target_role']}",
            "target_date": "2099-12-31",
        }
        for student in STUDENTS
    ]


def _student_project_records() -> list[dict[str, Any]]:
    return [
        {
            **student,
            "project_id": f"seed-project-{student['id']}",
            "project_title": f"{student['name']}'s learning portfolio",
            "project_url": f"https://example.org/projects/{student['id']}",
            "tech_stack": [],
            "project_description": "Synthetic starter project for local development.",
        }
        for student in STUDENTS
    ]


def bootstrap_graph(graph: GraphClient) -> dict[str, int]:
    """Idempotently initialize indexes and demo nodes/relationships."""
    ensure_range_indexes(graph)
    graph.query(STUDENT_QUERY, {"students": list(STUDENTS)})
    graph.query(
        SKILL_QUERY,
        {"skills": [{"name": name, "category": category} for name, category in SKILLS]},
    )
    graph.query(EVENT_QUERY, {"events": _event_records()})
    graph.query(COURSE_QUERY, {"courses": _course_records()})
    graph.query(
        STUDENT_SKILL_QUERY,
        {
            "student_skills": [
                {"student_id": student_id, "skill_name": skill, "proficiency": level}
                for student_id, skill, level in STUDENT_SKILLS
            ]
        },
    )
    graph.query(STUDENT_GOAL_QUERY, {"students": _student_goal_records()})
    graph.query(STUDENT_PROJECT_QUERY, {"students": _student_project_records()})
    graph.query(
        COURSE_SKILL_QUERY,
        {
            "course_skills": [
                {"course_id": course_id, "skill_name": skill}
                for course_id, skill in COURSE_SKILLS
            ]
        },
    )
    graph.query(
        PREREQUISITE_QUERY,
        {
            "prerequisites": [
                {"prerequisite": prerequisite, "skill": skill}
                for prerequisite, skill in SKILL_PREREQUISITES
            ]
        },
    )
    return {
        entity: graph.query(query).result_set[0][0]
        for entity, query in COUNT_QUERIES.items()
    }


def main() -> None:
    counts = bootstrap_graph(get_graph())
    expected = {
        "students": len(STUDENTS),
        "skills": len(SKILLS),
        "events": len(EVENTS),
        "courses": len(COURSES),
    }
    if counts != expected:
        raise RuntimeError(
            f"Graph bootstrap counts do not match the seed data: "
            f"expected {expected}, got {counts}"
        )
    print(f"FalkorDB graph initialized successfully: {counts}")
    print("Seed opportunities use example.org URLs and are demo data, not live listings.")


if __name__ == "__main__":
    main()
