import unittest

from fastapi.testclient import TestClient

from backend.agents.orchestrator import StudentProfileNotFoundError
from backend.api.dependencies import get_chat_orchestrator
from backend.main import app


class MissingStudentOrchestrator:
    def invoke(self, student_id: str, message: str) -> dict[str, object]:
        raise StudentProfileNotFoundError(f"Student {student_id!r} does not exist")


class ChatApiTests(unittest.TestCase):
    def tearDown(self) -> None:
        app.dependency_overrides.clear()

    def test_missing_profile_returns_actionable_error(self) -> None:
        app.dependency_overrides[get_chat_orchestrator] = (
            lambda: MissingStudentOrchestrator()
        )

        response = TestClient(app).post(
            "/api/v1/chat/message",
            json={"student_id": "unknown-student", "message": "Hello"},
        )

        self.assertEqual(response.status_code, 404)
        self.assertIn("Create a profile", response.json()["detail"])


if __name__ == "__main__":
    unittest.main()
