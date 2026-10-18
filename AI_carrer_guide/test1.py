import sys; sys.path.insert(0, "."); from backend.config.db import get_graph; print(type(get_graph()).__name__)
