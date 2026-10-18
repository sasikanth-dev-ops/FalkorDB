import hashlib
import re
from datetime import date, datetime
from typing import Any
from urllib.parse import urlparse

from pydantic import BaseModel, Field, HttpUrl, field_validator


def _strip_html(value: str) -> str:
    text = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", value)).strip()
    return re.sub(r"\s+([.,;:!?])", r"\1", text)


def _as_string(value: Any) -> str | None:
    if isinstance(value, str):
        cleaned = value.strip()
        return cleaned or None
    if isinstance(value, list):
        parts = [part for item in value if (part := _as_string(item))]
        return ", ".join(parts) or None
    if isinstance(value, dict):
        return _as_string(value.get("name") or value.get("url"))
    return None


def _normalize_deadline(value: Any) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return None
    candidate = value.strip()
    try:
        parsed = datetime.fromisoformat(candidate.replace("Z", "+00:00"))
        return parsed.date().isoformat()
    except ValueError:
        try:
            return date.fromisoformat(candidate).isoformat()
        except ValueError:
            return None


def _stable_opportunity_id(platform: str, url: str) -> str:
    canonical_url = url.split("#", maxsplit=1)[0].rstrip("/")
    digest = hashlib.sha256(f"{platform.lower()}:{canonical_url}".encode()).hexdigest()
    return f"opp-{digest[:24]}"


class NormalizedOpportunity(BaseModel):
    id: str = Field(min_length=1, max_length=100)
    title: str = Field(min_length=1, max_length=300)
    type: str = Field(min_length=1, max_length=50)
    platform: str = Field(min_length=1, max_length=100)
    deadline: str | None = None
    url: HttpUrl
    category: str | None = Field(default=None, max_length=100)
    description: str | None = Field(default=None, max_length=5000)
    required_skills: list[str] = Field(default_factory=list, max_length=100)

    @field_validator("required_skills")
    @classmethod
    def validate_skills(cls, values: list[str]) -> list[str]:
        normalized = []
        seen = set()
        for value in values:
            skill = value.strip()
            key = skill.casefold()
            if skill and key not in seen:
                normalized.append(skill[:100])
                seen.add(key)
        return normalized

    def graph_record(self) -> dict[str, Any]:
        record = self.model_dump(mode="json")
        record["url"] = str(self.url)
        return record


def normalize_opportunity(
    raw: dict[str, Any], *, platform: str, default_type: str = "Opportunity"
) -> NormalizedOpportunity:
    title = _as_string(raw.get("title") or raw.get("name"))
    url = _as_string(raw.get("url") or raw.get("link"))
    if not title:
        raise ValueError("Opportunity is missing a title")
    if not url:
        raise ValueError(f"Opportunity {title!r} is missing a URL")

    raw_skills = (
        raw.get("required_skills")
        or raw.get("skills_required")
        or raw.get("skills")
        or raw.get("technologies")
        or []
    )
    if isinstance(raw_skills, str):
        raw_skills = [item.strip() for item in raw_skills.split(",")]
    elif not isinstance(raw_skills, list):
        raw_skills = []

    skills = [
        skill
        for item in raw_skills
        if (skill := _as_string(item)) is not None
    ]
    description = _as_string(raw.get("description") or raw.get("summary"))
    if description:
        description = _strip_html(description)[:5000] or None
    category = _as_string(raw.get("category") or raw.get("industry"))
    opportunity_type = (
        _as_string(raw.get("opportunity_type") or raw.get("type")) or default_type
    )
    if opportunity_type.casefold() in {"event", "schema:event"}:
        opportunity_type = default_type

    return NormalizedOpportunity(
        id=_stable_opportunity_id(platform, url),
        title=title[:300],
        type=opportunity_type[:50],
        platform=platform,
        deadline=_normalize_deadline(
            raw.get("deadline") or raw.get("endDate") or raw.get("end_date")
        ),
        url=url,
        category=category,
        description=description,
        required_skills=skills,
    )


def validate_source_url(url: str, allowed_hosts: tuple[str, ...]) -> str:
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.hostname:
        raise ValueError("Configured scrape URLs must use HTTPS")
    hostname = parsed.hostname.casefold()
    if not any(
        hostname == host or hostname.endswith(f".{host}")
        for host in allowed_hosts
    ):
        raise ValueError(f"Scrape URL host {hostname!r} is not allowed for this source")
    return url
