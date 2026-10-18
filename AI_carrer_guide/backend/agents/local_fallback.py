from urllib.parse import urlparse

from backend.agents.memory_extractor import ChatIntent, MemoryExtraction

MERN_RESOURCES = (
    ("JavaScript", "https://www.freecodecamp.org/learn/javascript-algorithms-and-data-structures-v8/"),
    ("React", "https://react.dev/learn"),
    ("Node.js", "https://nodejs.org/en/learn"),
    ("Express", "https://expressjs.com/en/starter/hello-world.html"),
    ("MongoDB", "https://learn.mongodb.com/"),
)


def extract_local_intent(message: str) -> MemoryExtraction:
    text = message.casefold()
    if any(term in text for term in ("roadmap", "learn", "learning", "resource", "course", "study")):
        intent = ChatIntent.roadmap
    elif any(term in text for term in ("opportunit", "hackathon", "bounty", "internship")):
        intent = ChatIntent.opportunities
    else:
        intent = ChatIntent.general
    return MemoryExtraction(intent=intent)


def compose_local_reply(
    *,
    message: str,
    intent: ChatIntent,
    opportunities: list[dict[str, object]],
    roadmap: list[dict[str, object]],
) -> str:
    text = message.casefold()
    lines = [
        "**Gemini is unavailable right now, so this response uses local guidance. "
        "Any profile updates are shown separately.**"
    ]

    if "mern" in text:
        lines.extend(
            [
                "For MERN, learn the pieces in this order: JavaScript, React, Node.js, "
                "Express, then MongoDB. Build a small CRUD app as you go.",
                "Official learning resources:",
                *[
                    f"- [{name}]({url})"
                    for name, url in MERN_RESOURCES
                ],
            ]
        )
    elif intent is ChatIntent.opportunities:
        if opportunities:
            lines.append("Current graph recommendations:")
            lines.extend(
                f"- [{item.get('title', 'Opportunity')}]({item.get('url', '')})"
                for item in opportunities[:3]
                if item.get("url")
                and urlparse(str(item["url"])).hostname != "example.org"
            )
        else:
            lines.append(
                "There are no current verified opportunities matching this request "
                "in the local graph."
            )
    elif roadmap:
        lines.append("Your graph-based next steps:")
        for step in roadmap[:5]:
            resource = step.get("resource")
            title = resource.get("title") if isinstance(resource, dict) else None
            url = resource.get("url") if isinstance(resource, dict) else None
            action = f"{step.get('step')}. {step.get('action', step.get('skill', 'Learn next'))}"
            lines.append(f"- {action}" + (f" — [{title}]({url})" if title and url else ""))
    else:
        lines.append(
            "Try the learning-resource prompts for MERN, or retry your request after "
            "Gemini service access is restored."
        )

    return "\n\n".join(lines)
