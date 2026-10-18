"""Parameterized Cypher reads for API and application services."""

from datetime import date
from typing import Any, Protocol


class QueryResult(Protocol):
    result_set: list[list[Any]]


class GraphClient(Protocol):
    def query(
        self, query: str, params: dict[str, Any] | None = None
    ) -> QueryResult: ...


def get_student_profile(graph: GraphClient, student_id: str) -> dict[str, Any] | None:
    result = graph.query(
        """
        MATCH (s:Student {id: $student_id})
        OPTIONAL MATCH (s)-[skill_edge:HAS_SKILL]->(skill:Skill)
        WITH s, collect(DISTINCT CASE WHEN skill IS NULL THEN null ELSE {
            name: skill.name,
            category: skill.category,
            proficiency: skill_edge.proficiency
        } END) AS skills
        OPTIONAL MATCH (s)-[:HAS_GOAL]->(goal:Goal)
        WITH s, skills, collect(DISTINCT CASE WHEN goal IS NULL THEN null ELSE {
            id: goal.id,
            description: goal.description,
            target_date: goal.target_date
        } END) AS goals
        OPTIONAL MATCH (s)-[:BUILDING_PROJECT]->(project:Project)
        RETURN s.id AS student_id,
               s.name AS name,
               s.branch AS branch,
               s.year AS year,
               s.target_role AS target_role,
               skills,
               goals,
               collect(DISTINCT CASE WHEN project IS NULL THEN null ELSE {
                   id: project.id,
                   title: project.title,
                   repo_url: project.repo_url,
                   tech_stack: project.tech_stack
               } END) AS projects
        """,
        {"student_id": student_id},
    )
    if not result.result_set:
        return None
    row = result.result_set[0]
    return {
        "student_id": row[0],
        "name": row[1],
        "branch": row[2],
        "year": row[3],
        "target_role": row[4],
        "skills": _without_nulls(row[5]),
        "goals": _without_nulls(row[6]),
        "projects": _without_nulls(row[7]),
    }


def list_opportunities(
    graph: GraphClient,
    *,
    student_id: str | None = None,
    event_type: str | None = None,
    category: str | None = None,
    limit: int = 20,
    include_demo: bool = False,
) -> list[dict[str, Any]]:
    result = graph.query(
        """
        MATCH (event:Event)
        WHERE ($event_type IS NULL OR event.type = $event_type)
          AND ($category IS NULL OR event.category = $category)
          AND ($include_demo OR NOT event.url STARTS WITH 'https://example.org/')
          AND (event.deadline IS NULL OR event.deadline >= $today)
        OPTIONAL MATCH (student:Student {id: $student_id})
               -[:HAS_SKILL]->(matched:Skill)<-[:REQUIRES_SKILL]-(event)
        WITH event, collect(DISTINCT matched.name) AS matched_skills
        OPTIONAL MATCH (event)-[:REQUIRES_SKILL]->(required:Skill)
        WITH event, matched_skills, collect(DISTINCT required.name) AS required_skills
        RETURN event.id AS id,
               event.title AS title,
               event.type AS type,
               event.platform AS platform,
               event.deadline AS deadline,
               event.url AS url,
               event.category AS category,
               event.description AS description,
               required_skills,
               matched_skills
        ORDER BY event.deadline ASC
        LIMIT $limit
        """,
        {
            "student_id": student_id,
            "event_type": event_type,
            "category": category,
            "limit": limit,
            "include_demo": include_demo,
            "today": date.today().isoformat(),
        },
    )
    opportunities: list[dict[str, Any]] = []
    for row in result.result_set:
        required = _without_nulls(row[8])
        matched = _without_nulls(row[9])
        missing = [skill for skill in required if skill not in matched]
        match_percentage = (len(matched) / len(required) * 100) if required else None
        opportunities.append(
            {
                "id": row[0],
                "title": row[1],
                "type": row[2],
                "platform": row[3],
                "deadline": row[4],
                "url": row[5],
                "category": row[6],
                "description": row[7],
                "required_skills": required,
                "matched_skills": matched,
                "missing_skills": missing,
                "match_percentage": match_percentage if student_id else None,
                "prerequisite_paths": [],
            }
        )

    if student_id and opportunities:
        opportunities_by_id = {item["id"]: item for item in opportunities}
        paths = graph.query(
            """
            MATCH (student:Student {id: $student_id})-[:HAS_SKILL]->(known:Skill)
            MATCH path = (known)-[:PREREQUISITE_FOR*1..3]->(required:Skill)
            MATCH (event:Event)-[:REQUIRES_SKILL]->(required)
            WHERE event.id IN $opportunity_ids
            RETURN event.id AS opportunity_id,
                   known.name AS known_skill,
                   [skill IN nodes(path) | skill.name] AS skill_path
            ORDER BY opportunity_id, known_skill
            LIMIT 300
            """,
            {
                "student_id": student_id,
                "opportunity_ids": [item["id"] for item in opportunities],
            },
        )
        best_paths: dict[tuple[str, str], dict[str, Any]] = {}
        for opportunity_id, known_skill, skill_path in paths.result_set:
            if not skill_path or len(skill_path) < 2:
                continue
            opportunity = opportunities_by_id.get(opportunity_id)
            if opportunity is None or skill_path[-1] not in opportunity["missing_skills"]:
                continue
            key = (opportunity_id, skill_path[-1])
            evidence = {
                "known_skill": known_skill,
                "target_skill": skill_path[-1],
                "path": skill_path,
            }
            current = best_paths.get(key)
            if current is None or (
                len(skill_path),
                tuple(skill_path),
            ) < (
                len(current["path"]),
                tuple(current["path"]),
            ):
                best_paths[key] = evidence

        for (opportunity_id, _), evidence in best_paths.items():
            opportunities_by_id[opportunity_id]["prerequisite_paths"].append(
                evidence
            )

    return opportunities


def get_student_graph(graph: GraphClient, student_id: str) -> dict[str, Any] | None:
    student_result = graph.query(
        """
        MATCH (student:Student {id: $student_id})
        RETURN id(student) AS student_node_id,
               labels(student) AS student_labels,
               properties(student) AS student_properties
        """,
        {"student_id": student_id},
    )
    if not student_result.result_set:
        return None

    row = student_result.result_set[0]
    student_node_id, student_labels, student_properties = row
    edge_result = graph.query(
        """
        MATCH (student:Student {id: $student_id})
        MATCH path = (student)-[*1..2]-(neighbor)
        UNWIND relationships(path) AS edge
        WITH DISTINCT edge
        RETURN id(edge) AS id,
               id(startNode(edge)) AS source,
               id(endNode(edge)) AS target,
               type(edge) AS type,
               properties(edge) AS properties,
               labels(startNode(edge)) AS source_labels,
               properties(startNode(edge)) AS source_properties,
               labels(endNode(edge)) AS target_labels,
               properties(endNode(edge)) AS target_properties
        LIMIT 500
        """,
        {"student_id": student_id},
    )
    nodes: dict[str, dict[str, Any]] = {
        str(student_node_id): {
            "id": str(student_node_id),
            "labels": student_labels,
            "properties": student_properties,
        }
    }
    edges: dict[str, dict[str, Any]] = {}
    for edge in edge_result.result_set:
        source = str(edge[1])
        target = str(edge[2])
        nodes[source] = {
            "id": source,
            "labels": edge[5],
            "properties": edge[6],
        }
        nodes[target] = {
            "id": target,
            "labels": edge[7],
            "properties": edge[8],
        }
        edge_id = str(edge[0])
        edges[edge_id] = {
            "id": edge_id,
            "source": source,
            "target": target,
            "type": edge[3],
            "properties": edge[4],
        }
    return {"student_id": student_id, "nodes": list(nodes.values()), "edges": list(edges.values())}


def get_courses_for_skills(graph: GraphClient, skills: list[str]) -> list[dict[str, Any]]:
    if not skills:
        return []
    result = graph.query(
        """
        UNWIND $skills AS skill_name
        MATCH (course:Course)-[:TEACHES_SKILL]->(skill:Skill {name: skill_name})
        RETURN DISTINCT skill.name AS skill,
               course.title AS title,
               course.provider AS provider,
               course.duration_hours AS duration_hours,
               course.url AS url
        ORDER BY skill, title
        """,
        {"skills": skills},
    )
    return [
        {
            "skill": row[0],
            "title": row[1],
            "provider": row[2],
            "duration_hours": row[3],
            "url": row[4],
        }
        for row in result.result_set
    ]


def _without_nulls(values: Any) -> list[Any]:
    if values is None:
        return []
    return [value for value in values if value is not None]
