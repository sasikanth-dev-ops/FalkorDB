"""Canonical labels, relationship names, and graph indexes."""

NODE_LABELS = (
    "Student",
    "Skill",
    "Goal",
    "Project",
    "Event",
    "Course",
)

RELATIONSHIP_TYPES = (
    "HAS_SKILL",
    "HAS_GOAL",
    "BUILDING_PROJECT",
    "REQUIRES_SKILL",
    "TEACHES_SKILL",
    "PREREQUISITE_FOR",
    "LIKES_EVENT",
)

# Properties queried frequently by the profile and opportunity endpoints.
RANGE_INDEXES = {
    "Student": ("id",),
    "Skill": ("name",),
    "Goal": ("id",),
    "Project": ("id",),
    "Event": ("id", "title", "deadline"),
    "Course": ("title",),
}
