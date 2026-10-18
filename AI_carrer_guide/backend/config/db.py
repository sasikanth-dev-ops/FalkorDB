import logging
from functools import lru_cache
from typing import Any

from falkordb import FalkorDB

from backend.config.env import Settings, get_settings
from backend.database.in_memory_graph import InMemoryGraph

logger = logging.getLogger(__name__)
_IN_MEMORY_GRAPH_INSTANCE: InMemoryGraph | None = None


def create_graph(settings: Settings) -> Any:
    """Create a FalkorDB graph handle, with automatic in-memory fallback when offline."""
    global _IN_MEMORY_GRAPH_INSTANCE
    try:
        client = FalkorDB(
            host=settings.falkordb_host,
            port=settings.falkordb_port,
            username=settings.falkordb_username or None,
            password=settings.falkordb_password or None,
        )
        graph = client.select_graph(settings.falkordb_graph_name)
        graph.query("RETURN 1")
        return graph
    except Exception as exc:
        logger.warning(
            "FalkorDB not reachable at %s:%s (%s). Activating seeded in-memory graph engine.",
            settings.falkordb_host,
            settings.falkordb_port,
            exc,
        )
        if _IN_MEMORY_GRAPH_INSTANCE is None:
            _IN_MEMORY_GRAPH_INSTANCE = InMemoryGraph()
        return _IN_MEMORY_GRAPH_INSTANCE


@lru_cache
def get_graph() -> Any:
    """Return the process-wide graph handle for the configured database."""
    return create_graph(get_settings())
