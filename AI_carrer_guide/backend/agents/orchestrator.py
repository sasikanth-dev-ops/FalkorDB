import hashlib
from time import perf_counter
from typing import Any
from uuid import NAMESPACE_URL, uuid5

from langgraph.graph import END, START, StateGraph

from backend.agents import audit_logger
from backend.agents.local_fallback import compose_local_reply, extract_local_intent
from backend.agents.memory_extractor import (
    GeminiMemoryExtractor,
    GeminiReplyGenerator,
    ModelClient,
    ModelOutputError,
)
from backend.agents.planner import plan_after_memory_extraction, plan_after_retrieval
from backend.agents.readiness_evaluator import evaluate_readiness
from backend.agents.roadmap_generator import generate_roadmap
from backend.agents.state import ChatState
from backend.database import read_ops, write_ops
from backend.database.read_ops import GraphClient

class StudentProfileNotFoundError(Exception):
    """Raised only when the requested student profile does not exist."""
class ChatOrchestrator:
    def __init__(self, graph: GraphClient, client: ModelClient, model: str) -> None:
        self._graph = graph
        self._extractor = GeminiMemoryExtractor(client, model)
        self._reply_generator = GeminiReplyGenerator(client, model)

        workflow = StateGraph(ChatState)
        workflow.add_node("extract_memories", self._extract_memories)
        workflow.add_node("persist_memories", self._persist_memories)
        workflow.add_node("retrieve_opportunities", self._retrieve_opportunities)
        workflow.add_node("generate_roadmap", self._generate_roadmap)
        workflow.add_node("compose_response", self._compose_response)
        workflow.add_edge(START, "extract_memories")
        workflow.add_edge("extract_memories", "persist_memories")
        workflow.add_conditional_edges(
            "persist_memories",
            lambda state: plan_after_memory_extraction(state["extraction"].intent),
            {
                "retrieve_opportunities": "retrieve_opportunities",
                "compose_response": "compose_response",
            },
        )
        workflow.add_conditional_edges(
            "retrieve_opportunities",
            lambda state: plan_after_retrieval(state["extraction"].intent),
            {
                "generate_roadmap": "generate_roadmap",
                "compose_response": "compose_response",
            },
        )
        workflow.add_edge("generate_roadmap", "compose_response")
        workflow.add_edge("compose_response", END)
        self._workflow = workflow.compile()

    def invoke(self, student_id: str, message: str) -> dict[str, Any]:
        started_at = perf_counter()
        profile = read_ops.get_student_profile(self._graph, student_id)
        if profile is None:
            raise StudentProfileNotFoundError(f"Student {student_id!r} does not exist")

        final_state = self._workflow.invoke(
            {"student_id": student_id, "message": message, "profile": profile}
        )
        result = {
            "student_id": student_id,
            "message": final_state["response"],
            "intent": final_state["extraction"].intent.value,
            "memory_updates": {
                "skills": [skill.name for skill in final_state["extraction"].skills],
                "goals": [
                    goal.description for goal in final_state["extraction"].goals
                ],
                "projects": [project.title for project in final_state["extraction"].projects],
            },
            "opportunities": final_state["opportunities"],
            "roadmap": final_state["roadmap"],
            "profile": final_state["updated_profile"],
            "model_degraded": final_state.get("model_degraded", False),
        }
        audit_logger.log_chat_completed(
            student_id=student_id,
            intent=result["intent"],
            skill_updates=len(result["memory_updates"]["skills"]),
            goal_updates=len(result["memory_updates"]["goals"]),
            project_updates=len(result["memory_updates"]["projects"]),
            opportunity_count=len(result["opportunities"]),
            duration_ms=round((perf_counter() - started_at) * 1000),
        )
        return result

    def _extract_memories(self, state: ChatState) -> dict[str, Any]:
        try:
            extraction = self._extractor.extract(state["message"], state["profile"])
            return {"extraction": extraction}
        except ModelOutputError as exc:
            audit_logger.logger.warning(
                "Gemini memory extraction failed; using local intent only: %s", exc
            )
            return {
                "extraction": extract_local_intent(state["message"]),
                "model_degraded": True,
            }

    def _persist_memories(self, state: ChatState) -> dict[str, Any]:
        extraction = state["extraction"]
        memories = extraction.model_dump(mode="json")
        for goal in memories["goals"]:
            goal["goal_id"] = self._stable_id(state["student_id"], "goal", goal["description"])
        for project in memories["projects"]:
            project["project_id"] = self._stable_id(state["student_id"], "project", project["title"])
        write_ops.save_chat_memories(self._graph, state["student_id"], memories)
        updated_profile = read_ops.get_student_profile(self._graph, state["student_id"])
        if updated_profile is None:
            raise RuntimeError("Student profile disappeared after memory update")
        return {"updated_profile": updated_profile}

    def _retrieve_opportunities(self, state: ChatState) -> dict[str, Any]:
        intent = state["extraction"].intent.value
        if intent not in {"opportunities", "roadmap"}:
            return {"opportunities": []}
        message = state["message"]
        event_type = (
            "Hackathon" if "hackathon" in message.casefold() else None
        )
        return {
            "opportunities": evaluate_readiness(
                self._graph,
                state["student_id"],
                limit=5,
                query=message,
                event_type=event_type,
            )
        }

    def _generate_roadmap(self, state: ChatState) -> dict[str, Any]:
        if state["extraction"].intent.value != "roadmap":
            return {"roadmap": []}
        return {
            "roadmap": generate_roadmap(self._graph, state["opportunities"])
        }

    def _compose_response(self, state: ChatState) -> dict[str, Any]:
        if state.get("model_degraded"):
            return {
                "response": compose_local_reply(
                    message=state["message"],
                    intent=state["extraction"].intent,
                    opportunities=state["opportunities"],
                    roadmap=state["roadmap"],
                )
            }
        try:
            response = self._reply_generator.generate(
                message=state["message"],
                profile=state["updated_profile"],
                opportunities=state["opportunities"],
                roadmap=state["roadmap"],
            )
            return {"response": response}
        except ModelOutputError as exc:
            audit_logger.logger.warning(
                "Gemini reply generation failed; using local response: %s", exc
            )
            return {
                "response": compose_local_reply(
                    message=state["message"],
                    intent=state["extraction"].intent,
                    opportunities=state["opportunities"],
                    roadmap=state["roadmap"],
                ),
                "model_degraded": True,
            }

    @staticmethod
    def _stable_id(student_id: str, kind: str, value: str) -> str:
        normalized = " ".join(value.lower().split())
        digest = hashlib.sha256(f"{student_id}:{kind}:{normalized}".encode()).hexdigest()
        return str(uuid5(NAMESPACE_URL, digest))
