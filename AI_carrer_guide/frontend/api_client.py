"""FastAPI backend client for the AI Career Mentor Streamlit dashboard."""

from __future__ import annotations

import os
from typing import Any

import requests

DEFAULT_BACKEND_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")


class CareerMentorAPIClient:
    def __init__(self, base_url: str = DEFAULT_BACKEND_URL, timeout: float = 25.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_prefix = f"{self.base_url}/api/v1"
        self.timeout = timeout

    def check_health(self) -> dict[str, Any]:
        try:
            res = requests.get(f"{self.base_url}/health", timeout=4.0)
            if res.status_code == 200:
                return {"status": "connected", "details": res.json()}
            return {"status": "error", "code": res.status_code, "details": res.text}
        except Exception as exc:
            return {"status": "offline", "error": str(exc)}

    def get_student_profile(self, student_id: str) -> dict[str, Any] | None:
        try:
            res = requests.get(f"{self.api_prefix}/student/{student_id}", timeout=self.timeout)
            if res.status_code == 200:
                return res.json()
            return None
        except Exception:
            return None

    def save_student_profile(self, profile: dict[str, Any]) -> dict[str, Any] | None:
        try:
            res = requests.post(f"{self.api_prefix}/student/profile", json=profile, timeout=self.timeout)
            if res.status_code == 200:
                return res.json()
            return None
        except Exception:
            return None

    def get_opportunities(
        self,
        student_id: str | None = None,
        query: str | None = None,
        event_type: str | None = None,
        category: str | None = None,
        limit: int = 20,
        include_demo: bool = False,
    ) -> list[dict[str, Any]]:
        params: dict[str, Any] = {
            "limit": limit,
            "include_demo": include_demo,
        }
        if student_id:
            params["student_id"] = student_id
        if query and query.strip():
            params["query"] = query.strip()
        if event_type and event_type != "All":
            params["type"] = event_type
        if category and category != "All":
            params["category"] = category

        try:
            res = requests.get(f"{self.api_prefix}/opportunities", params=params, timeout=self.timeout)
            if res.status_code == 200:
                return res.json()
            return []
        except Exception:
            return []

    def get_graph_state(self, student_id: str) -> dict[str, Any] | None:
        try:
            res = requests.get(f"{self.api_prefix}/graph/state/{student_id}", timeout=self.timeout)
            if res.status_code == 200:
                return res.json()
            return None
        except Exception:
            return None

    def get_roadmap(self, student_id: str) -> list[dict[str, Any]]:
        try:
            res = requests.get(f"{self.api_prefix}/roadmap", params={"student_id": student_id}, timeout=self.timeout)
            if res.status_code == 200:
                return res.json()
            return []
        except Exception:
            return []

    def send_chat_message(self, student_id: str, message: str) -> dict[str, Any]:
        try:
            res = requests.post(
                f"{self.api_prefix}/chat/message",
                json={"student_id": student_id, "message": message},
                timeout=self.timeout,
            )
            if res.status_code == 200:
                return {"success": True, "data": res.json()}
            if res.status_code == 503:
                return {"success": False, "error": "AI Mentor service is unavailable (check GEMINI_API_KEY)."}
            return {"success": False, "error": f"API returned status {res.status_code}: {res.text}"}
        except Exception as exc:
            return {"success": False, "error": f"Failed to connect to backend: {exc}"}

    def scrape_sources(self, sources: list[str]) -> dict[str, Any]:
        try:
            res = requests.post(
                f"{self.api_prefix}/opportunities/scrape",
                json={"sources": sources},
                timeout=self.timeout,
            )
            if res.status_code == 200:
                return {"success": True, "data": res.json()}
            return {"success": False, "error": res.text}
        except Exception as exc:
            return {"success": False, "error": str(exc)}
