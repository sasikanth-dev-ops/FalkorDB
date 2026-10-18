"""In-memory GraphClient fallback for development, offline demoing, and evaluation.

Provides seamless continuity when FalkorDB / Docker Desktop is not actively running.
"""

from __future__ import annotations

import logging
from typing import Any

from backend.database import seed_data

logger = logging.getLogger(__name__)


class QueryResult:
    def __init__(self, result_set: list[list[Any]]) -> None:
        self.result_set = result_set


class InMemoryGraph:
    """In-memory GraphClient implementation loaded with seed entities and relationships."""

    def __init__(self) -> None:
        self._students: dict[str, dict[str, Any]] = {}
        self._skills: dict[str, dict[str, Any]] = {}
        self._events: dict[str, dict[str, Any]] = {}
        self._courses: dict[str, dict[str, Any]] = {}

        # Edges
        # student_id -> list of {"name": skill, "proficiency": prof, "category": cat}
        self._student_skills: dict[str, dict[str, str]] = {}
        # student_id -> list of goals
        self._student_goals: dict[str, list[dict[str, Any]]] = {}
        # student_id -> list of projects
        self._student_projects: dict[str, list[dict[str, Any]]] = {}
        # event_id -> set of required skill names
        self._event_skills: dict[str, list[str]] = {}
        # prerequisite skill -> skills it prepares the student to learn
        self._skill_prerequisites: dict[str, list[str]] = {}
        # skill_name -> list of courses
        self._course_skills: dict[str, list[dict[str, Any]]] = {}

        self._load_seed_data()

    def list_indices(self) -> QueryResult:
        """Return empty index list for in-memory implementation."""
        return QueryResult([])

    def create_node_range_index(self, label: str, *properties: str) -> None:
        """No-op for in-memory implementation - indexes not needed."""
        logger.debug(f"In-memory graph: skipping index creation for {label}({', '.join(properties)})")


    def _load_seed_data(self) -> None:
        for s in seed_data.STUDENTS:
            self._students[s["id"]] = dict(s)
            self._student_skills[s["id"]] = {}
            self._student_goals[s["id"]] = []
            self._student_projects[s["id"]] = []

        for name, cat in seed_data.SKILLS:
            self._skills[name] = {"name": name, "category": cat}

        for ev in seed_data.EVENTS:
            self._events[ev["id"]] = dict(ev)
            self._event_skills[ev["id"]] = list(ev.get("skills", ()))

        for c_id, title, provider, duration, url in seed_data.COURSES:
            self._courses[c_id] = {
                "id": c_id,
                "title": title,
                "provider": provider,
                "duration_hours": duration,
                "url": url,
            }

        for s_id, skill, prof in seed_data.STUDENT_SKILLS:
            if s_id in self._students:
                self._student_skills[s_id][skill] = prof

        for c_id, skill in seed_data.COURSE_SKILLS:
            if skill not in self._course_skills:
                self._course_skills[skill] = []
            if c_id in self._courses:
                course_record = dict(self._courses[c_id])
                course_record["skill"] = skill
                self._course_skills[skill].append(course_record)

        for prerequisite, skill in seed_data.SKILL_PREREQUISITES:
            self._skill_prerequisites.setdefault(prerequisite, []).append(skill)

        # Default goals & projects for seed-student-001
        self._student_goals["seed-student-001"] = [
            {"id": "goal-001", "description": "Compete in an AI hackathon", "target_date": "2026-11-30"},
            {"id": "goal-002", "description": "Master backend API design with FastAPI", "target_date": "2026-12-15"},
        ]
        self._student_projects["seed-student-001"] = [
            {
                "id": "proj-001",
                "title": "API Gateway Service",
                "repo_url": "https://github.com/example/api-gateway",
                "tech_stack": ["Python", "FastAPI", "Docker"],
            }
        ]

    def query(self, query: str, params: dict[str, Any] | None = None) -> QueryResult:
        params = params or {}
        q = " ".join(query.split())

        # Check student exists
        if "MATCH (student:Student {id: $student_id}) RETURN student.id" in q:
            sid = params.get("student_id")
            if sid in self._students:
                return QueryResult([[sid]])
            return QueryResult([])

        # Student Profile read
        if "MATCH (s:Student {id: $student_id})" in q and "OPTIONAL MATCH (s)-[skill_edge:HAS_SKILL]" in q:
            sid = params.get("student_id")
            if sid not in self._students:
                return QueryResult([])
            s = self._students[sid]
            skills_list = [
                {
                    "name": name,
                    "category": self._skills.get(name, {}).get("category", "General"),
                    "proficiency": prof,
                }
                for name, prof in self._student_skills.get(sid, {}).items()
            ]
            goals_list = self._student_goals.get(sid, [])
            projects_list = self._student_projects.get(sid, [])
            return QueryResult(
                [
                    [
                        s["id"],
                        s.get("name"),
                        s.get("branch"),
                        s.get("year"),
                        s.get("target_role"),
                        skills_list,
                        goals_list,
                        projects_list,
                    ]
                ]
            )

        if "MATCH path = (known)-[:PREREQUISITE_FOR*1..3]->(required:Skill)" in q:
            sid = params.get("student_id")
            known_skills = self._student_skills.get(sid, {})
            opportunity_ids = set(params.get("opportunity_ids", []))
            rows = []
            for known_skill in known_skills:
                pending = [(known_skill, [known_skill])]
                while pending:
                    skill, path = pending.pop()
                    if len(path) > 1:
                        for event_id, required_skills in self._event_skills.items():
                            if (
                                event_id in opportunity_ids
                                and skill in required_skills
                                and skill not in known_skills
                            ):
                                rows.append([event_id, known_skill, path])
                    if len(path) < 4:
                        for next_skill in reversed(
                            self._skill_prerequisites.get(skill, [])
                        ):
                            if next_skill not in path:
                                pending.append((next_skill, [*path, next_skill]))
            rows.sort(key=lambda row: (row[0], len(row[2]), row[1], tuple(row[2])))
            return QueryResult(rows[:300])

        if "UNWIND $opportunities AS row" in q:
            for opportunity in params.get("opportunities", []):
                event_id = opportunity["id"]
                event = self._events.setdefault(event_id, {"id": event_id})
                event.update(
                    {
                        key: opportunity.get(key)
                        for key in (
                            "title",
                            "type",
                            "platform",
                            "deadline",
                            "url",
                            "category",
                            "description",
                        )
                    }
                )
                skills = list(opportunity.get("required_skills", []))
                self._event_skills[event_id] = skills
                for skill_name in skills:
                    self._skills.setdefault(
                        skill_name, {"name": skill_name, "category": None}
                    )
            return QueryResult([])

        # Opportunities read
        if "MATCH (event:Event)" in q and "OPTIONAL MATCH (event)-[:REQUIRES_SKILL]" in q:
            sid = params.get("student_id")
            event_type = params.get("event_type")
            category = params.get("category")
            limit = params.get("limit", 20)
            include_demo = params.get("include_demo", False)
            today = params.get("today")

            student_known_skills = set(self._student_skills.get(sid, {}).keys()) if sid else set()
            rows = []
            for ev_id, ev in self._events.items():
                if (
                    not include_demo
                    and str(ev.get("url", "")).startswith("https://example.org/")
                ):
                    continue
                if ev.get("deadline") and today and ev["deadline"] < today:
                    continue
                if event_type and ev.get("type") != event_type:
                    continue
                if category and ev.get("category") != category:
                    continue

                req_skills = self._event_skills.get(ev_id, [])
                matched_skills = [sk for sk in req_skills if sk in student_known_skills]

                rows.append(
                    [
                        ev["id"],
                        ev["title"],
                        ev["type"],
                        ev.get("platform", "Platform"),
                        ev.get("deadline"),
                        ev.get("url", "#"),
                        ev.get("category"),
                        ev.get("description"),
                        req_skills,
                        matched_skills,
                    ]
                )
            rows.sort(key=lambda r: r[4] or "9999-12-31")
            return QueryResult(rows[:limit])

        # Student Graph state (nodes & edges)
        if "MATCH (student:Student {id: $student_id}) RETURN id(student)" in q:
            sid = params.get("student_id")
            if sid not in self._students:
                return QueryResult([])
            s = self._students[sid]
            return QueryResult([[sid, ["Student"], s]])

        if "MATCH path = (student)-[*1..2]-(neighbor)" in q:
            sid = params.get("student_id")
            s = self._students.get(sid, {})
            edges_rows = []
            # student -> skills
            for sk_name, prof in self._student_skills.get(sid, {}).items():
                sk_props = self._skills.get(sk_name, {"name": sk_name, "category": "General"})
                edges_rows.append(
                    [
                        f"{sid}-skill-{sk_name}",
                        sid,
                        sk_name,
                        "HAS_SKILL",
                        {"proficiency": prof},
                        ["Student"],
                        s,
                        ["Skill"],
                        sk_props,
                    ]
                )
            # student -> goals
            for goal in self._student_goals.get(sid, []):
                gid = goal.get("id") or goal.get("description", "goal")
                edges_rows.append(
                    [
                        f"{sid}-goal-{gid}",
                        sid,
                        gid,
                        "HAS_GOAL",
                        {},
                        ["Student"],
                        s,
                        ["Goal"],
                        goal,
                    ]
                )
            # student -> projects
            for proj in self._student_projects.get(sid, []):
                pid = proj.get("id") or proj.get("title", "project")
                edges_rows.append(
                    [
                        f"{sid}-proj-{pid}",
                        sid,
                        pid,
                        "BUILDING_PROJECT",
                        {},
                        ["Student"],
                        s,
                        ["Project"],
                        proj,
                    ]
                )
            return QueryResult(edges_rows)

        # Courses for skills
        if "UNWIND $skills AS skill_name" in q and "TEACHES_SKILL" in q:
            skills = params.get("skills", [])
            rows = []
            for sk in skills:
                for c in self._course_skills.get(sk, []):
                    rows.append([sk, c["title"], c["provider"], c["duration_hours"], c["url"]])
            return QueryResult(rows)

        # Upsert profile writes
        if "MERGE (s:Student {id: $student_id})" in q:
            sid = params.get("student_id")
            if sid:
                if sid not in self._students:
                    self._students[sid] = {"id": sid}
                    self._student_skills[sid] = {}
                    self._student_goals[sid] = []
                    self._student_projects[sid] = []
                self._students[sid].update(
                    {
                        "name": params.get("name"),
                        "branch": params.get("branch"),
                        "year": params.get("year"),
                        "target_role": params.get("target_role"),
                    }
                )
            return QueryResult([])

        # Skill writes
        if "MERGE (skill:Skill {name: $name})" in q and "MERGE (s)-[edge:HAS_SKILL]->(skill)" in q:
            sid = params.get("student_id")
            sk_name = params.get("name")
            prof = params.get("proficiency", "beginner")
            if sid and sk_name:
                if sid not in self._students:
                    self._students[sid] = {"id": sid}
                    self._student_skills[sid] = {}
                self._student_skills[sid][sk_name] = prof
                if sk_name not in self._skills:
                    self._skills[sk_name] = {"name": sk_name, "category": params.get("category", "General")}
            return QueryResult([])

        # Goal writes
        if "MERGE (g:Goal {id: $goal_id})" in q and "MERGE (s)-[:HAS_GOAL]->(g)" in q:
            sid = params.get("student_id")
            gid = params.get("goal_id")
            desc = params.get("description")
            if sid and desc:
                if sid not in self._student_goals:
                    self._student_goals[sid] = []
                self._student_goals[sid].append({"id": gid, "description": desc, "target_date": params.get("target_date")})
            return QueryResult([])

        # Project writes
        if "MERGE (p:Project {id: $project_id})" in q and "MERGE (s)-[:BUILDING_PROJECT]->(p)" in q:
            sid = params.get("student_id")
            pid = params.get("project_id")
            title = params.get("title")
            if sid and title:
                if sid not in self._student_projects:
                    self._student_projects[sid] = []
                self._student_projects[sid].append(
                    {
                        "id": pid,
                        "title": title,
                        "repo_url": params.get("repo_url"),
                        "tech_stack": params.get("tech_stack", []),
                    }
                )
            return QueryResult([])

        # Opportunities write
        if "UNWIND $events AS event_data" in q:
            events = params.get("events", [])
            for ev in events:
                eid = ev.get("id")
                if eid:
                    self._events[eid] = dict(ev)
                    req_skills = ev.get("required_skills", [])
                    self._event_skills[eid] = list(req_skills)
                    for sk in req_skills:
                        if sk not in self._skills:
                            self._skills[sk] = {"name": sk, "category": "General"}
            return QueryResult([[len(events)]])

        # Health / simple return
        return QueryResult([[1]])
