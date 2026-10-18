import unittest

from backend.database.seed_data import (
    COURSES,
    COURSE_SKILLS,
    EVENTS,
    SKILLS,
    STUDENTS,
    STUDENT_SKILLS,
)


class SeedDataTests(unittest.TestCase):
    def test_demo_seed_has_required_entity_counts(self) -> None:
        self.assertEqual(len(STUDENTS), 5)
        self.assertEqual(len(SKILLS), 20)
        self.assertEqual(len(EVENTS), 10)
        self.assertEqual(len(COURSES), 10)

    def test_seed_relationships_reference_existing_entities(self) -> None:
        student_ids = {student["id"] for student in STUDENTS}
        skill_names = {name for name, _ in SKILLS}
        course_ids = {course[0] for course in COURSES}

        self.assertTrue(all(student_id in student_ids for student_id, _, _ in STUDENT_SKILLS))
        self.assertTrue(all(skill in skill_names for _, skill, _ in STUDENT_SKILLS))
        self.assertTrue(
            all(
                skill in skill_names
                for event in EVENTS
                for skill in event["skills"]
            )
        )
        self.assertTrue(
            all(
                course_id in course_ids and skill in skill_names
                for course_id, skill in COURSE_SKILLS
            )
        )

    def test_demo_event_urls_are_not_presented_as_live_sources(self) -> None:
        self.assertTrue(
            all(event["url"].startswith("https://example.org/") for event in EVENTS)
        )


if __name__ == "__main__":
    unittest.main()
