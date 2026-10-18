from fastapi import APIRouter

from backend.api.routes import chat, graph, health, opportunities, roadmap, student

router = APIRouter()
router.include_router(health.router)
router.include_router(student.router)
router.include_router(opportunities.router)
router.include_router(roadmap.router)
router.include_router(graph.router)
router.include_router(chat.router)
