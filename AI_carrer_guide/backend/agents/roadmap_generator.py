from typing import Any

from backend.database.read_ops import GraphClient, get_courses_for_skills


def generate_roadmap(
    graph: GraphClient, opportunities: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    if not opportunities:
        return []

    target = opportunities[0]
    missing_skills = target["missing_skills"]
    direct_matches = set(target.get("matched_skills", []))
    paths_by_target: dict[str, list[list[str]]] = {}
    for evidence in target.get("prerequisite_paths", []):
        path = evidence.get("path", [])
        if (
            len(path) >= 2
            and path[0] == evidence.get("known_skill")
            and path[-1] == evidence.get("target_skill")
        ):
            paths_by_target.setdefault(path[-1], []).append(path)

    ordered_skills: list[str] = []
    for missing_skill in missing_skills:
        paths = paths_by_target.get(missing_skill, [])
        best_path = min(paths, key=lambda path: (len(path), tuple(path)), default=None)
        candidates = best_path[1:] if best_path else [missing_skill]
        for skill in candidates:
            if skill not in direct_matches and skill not in ordered_skills:
                ordered_skills.append(skill)

    if not ordered_skills:
        return []

    courses = get_courses_for_skills(graph, ordered_skills)
    course_by_skill = {course["skill"]: course for course in courses}
    return [
        {
            "step": index,
            "skill": skill,
            "action": f"Build foundational knowledge in {skill}",
            "resource": course_by_skill.get(skill),
            "target_opportunity_id": target["id"],
        }
        for index, skill in enumerate(ordered_skills, start=1)
    ]
