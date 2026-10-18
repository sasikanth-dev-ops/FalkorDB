
from contextlib import asynccontextmanager
from backend.database.in_memory_graph import InMemoryGraph
from fastapi import FastAPI
from backend.api.router import router
from backend.api.routes.health import router as health_router
from backend.config.db import get_graph
from backend.config.env import get_settings
from backend.database.setup import bootstrap_graph

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    graph = get_graph()

    if isinstance(graph, InMemoryGraph):
        # The in-memory graph is seeded separately.
        # Do not run FalkorDB-specific index/bootstrap operations.
        print("Using seeded in-memory graph; skipping FalkorDB bootstrap.")
    else:
        # Run schema and seed initialization only for real FalkorDB.
        bootstrap_graph(graph)

    yield


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="A persistent, graph-powered AI career mentor.",
    lifespan=lifespan,
)

app.include_router(
    router,
    prefix=settings.api_v1_prefix.rstrip("/"),
)
app.include_router(health_router)


@app.get("/", tags=["health"], include_in_schema=False)
def root() -> dict[str, str]:
    return {
        "name": settings.app_name,
        "docs": "/docs",
    }
