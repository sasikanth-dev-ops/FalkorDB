from backend.agents.memory_extractor import ChatIntent


def plan_after_memory_extraction(intent: ChatIntent) -> str:
    if intent in {ChatIntent.opportunities, ChatIntent.roadmap}:
        return "retrieve_opportunities"
    return "compose_response"


def plan_after_retrieval(intent: ChatIntent) -> str:
    if intent is ChatIntent.roadmap:
        return "generate_roadmap"
    return "compose_response"
