"""Parameterized Cypher mutations for student profile operations."""

from typing import Any, Protocol


class QueryResult(Protocol):
    result_set: list[list[Any]]


class GraphClient(Protocol):
    def query(
        self, query: str, params: dict[str, Any] | None = None
    ) -> QueryResult: ...


def save_student_profile(graph: GraphClient, profile: dict[str, Any]) -> str:
    graph.query(
        """
        MERGE (student:Student {id: $student_id})
        ON CREATE SET student.name = $name
        SET student.name = coalesce($name, student.name),
            student.branch = coalesce($branch, student.branch),
            student.year = coalesce($year, student.year),
            student.target_role = coalesce($target_role, student.target_role)
        """,
        {
            "student_id": profile["student_id"],
            "name": profile.get("name"),
            "branch": profile.get("branch"),
            "year": profile.get("year"),
            "target_role": profile.get("target_role"),
        },
    )

    for skill in profile.get("skills", []):
        graph.query(
            """
            MATCH (student:Student {id: $student_id})
            MERGE (node:Skill {name: $name})
            ON CREATE SET node.category = $category
            SET node.category = coalesce($category, node.category)
            MERGE (student)-[edge:HAS_SKILL]->(node)
            SET edge.proficiency = $proficiency,
                edge.updated_at = timestamp()
            """,
            {
                "student_id": profile["student_id"],
                "name": skill["name"],
                "category": skill.get("category"),
                "proficiency": skill["proficiency"],
            },
        )

    for goal in profile.get("goals", []):
        graph.query(
            """
            MATCH (student:Student {id: $student_id})
            MERGE (node:Goal {id: $goal_id})
            SET node.description = $description,
                node.target_date = $target_date
            MERGE (student)-[:HAS_GOAL]->(node)
            """,
            {
                "student_id": profile["student_id"],
                "goal_id": goal["goal_id"],
                "description": goal["description"],
                "target_date": goal.get("target_date"),
            },
        )
    return profile["student_id"]


def save_chat_memories(
    graph: GraphClient, student_id: str, memories: dict[str, Any]
) -> None:
    for skill in memories.get("skills", []):
        graph.query(
            """
            MATCH (student:Student {id: $student_id})
            MERGE (node:Skill {name: $name})
            ON CREATE SET node.category = $category
            SET node.category = coalesce($category, node.category)
            MERGE (student)-[edge:HAS_SKILL]->(node)
            SET edge.proficiency = $proficiency,
                edge.updated_at = timestamp()
            """,
            {
                "student_id": student_id,
                "name": skill["name"],
                "category": skill.get("category"),
                "proficiency": skill["proficiency"],
            },
        )

    for goal in memories.get("goals", []):
        graph.query(
            """
            MATCH (student:Student {id: $student_id})
            MERGE (node:Goal {id: $goal_id})
            SET node.description = $description,
                node.target_date = $target_date
            MERGE (student)-[:HAS_GOAL]->(node)
            """,
            {
                "student_id": student_id,
                "goal_id": goal["goal_id"],
                "description": goal["description"],
                "target_date": goal.get("target_date"),
            },
        )

    for project in memories.get("projects", []):
        graph.query(
            """
            MATCH (student:Student {id: $student_id})
            MERGE (node:Project {id: $project_id})
            SET node.title = $title,
                node.repo_url = $repo_url,
                node.tech_stack = $tech_stack,
                node.description = $description
            MERGE (student)-[:BUILDING_PROJECT]->(node)
            """,
            {
                "student_id": student_id,
                "project_id": project["project_id"],
                "title": project["title"],
                "repo_url": project.get("repo_url"),
                "tech_stack": project.get("tech_stack", []),
                "description": project.get("description"),
            },
        )


def upsert_opportunities(
    graph: GraphClient, opportunities: list[dict[str, Any]]
) -> int:
    if not opportunities:
        return 0

    graph.query(
        """
        UNWIND $opportunities AS row
        MERGE (event:Event {id: row.id})
        SET event.title = row.title,
            event.type = row.type,
            event.platform = row.platform,
            event.deadline = row.deadline,
            event.url = row.url,
            event.category = row.category,
            event.description = row.description
        """,
        {"opportunities": opportunities},
    )
    graph.query(
        """
        UNWIND $opportunities AS row
        MATCH (event:Event {id: row.id})
        WITH row, event
        OPTIONAL MATCH (event)-[old_requirement:REQUIRES_SKILL]->(old_skill:Skill)
        WHERE old_skill IS NULL OR NOT old_skill.name IN row.required_skills
        WITH row, event, collect(old_requirement) AS stale_requirements
        FOREACH (relationship IN stale_requirements | DELETE relationship)
        WITH row, event
        UNWIND row.required_skills AS skill_name
        MERGE (skill:Skill {name: skill_name})
        MERGE (event)-[:REQUIRES_SKILL]->(skill)
        """,
        {"opportunities": opportunities},
    )
    return len(opportunities)
