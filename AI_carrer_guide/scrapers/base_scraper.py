import json
from typing import Any

import requests
from bs4 import BeautifulSoup
from requests import Response

from scrapers.normalizer import NormalizedOpportunity, normalize_opportunity, validate_source_url

MAX_RESPONSE_BYTES = 5_000_000


class BaseScraper:
    platform: str
    allowed_hosts: tuple[str, ...]
    default_type = "Opportunity"

    def __init__(self, timeout_seconds: float = 15.0) -> None:
        self.timeout_seconds = timeout_seconds

    def scrape(self, url: str) -> list[NormalizedOpportunity]:
        validated_url = validate_source_url(url, self.allowed_hosts)
        response = requests.get(
            validated_url,
            headers={
                "Accept": "text/html,application/json",
                "User-Agent": "AICareerMentorOpportunityIndexer/1.0",
            },
            timeout=self.timeout_seconds,
            allow_redirects=False,
            stream=True,
        )
        with response:
            response.raise_for_status()
            if response.is_redirect:
                raise ValueError(
                    f"{self.platform} scrape URL redirected; configure its final HTTPS URL"
                )
            content_length = response.headers.get("Content-Length")
            if content_length and int(content_length) > MAX_RESPONSE_BYTES:
                raise ValueError(f"{self.platform} response exceeds the 5 MB limit")
            content = bytearray()
            for chunk in response.iter_content(chunk_size=64 * 1024):
                content.extend(chunk)
                if len(content) > MAX_RESPONSE_BYTES:
                    raise ValueError(f"{self.platform} response exceeds the 5 MB limit")
            response._content = bytes(content)
            response._content_consumed = True
            records = self.parse_response(response)
        return [
            normalize_opportunity(
                record, platform=self.platform, default_type=self.default_type
            )
            for record in records
        ]

    def parse_response(self, response: Response) -> list[dict[str, Any]]:
        content_type = response.headers.get("Content-Type", "").casefold()
        if "json" in content_type:
            payload = response.json()
            return self._json_records(payload)
        return self._json_ld_records(response.text)

    @classmethod
    def _json_records(cls, payload: Any) -> list[dict[str, Any]]:
        if isinstance(payload, list):
            return [record for record in payload if isinstance(record, dict)]
        if not isinstance(payload, dict):
            raise ValueError("Opportunity feed JSON must be an object or array")
        for key in ("opportunities", "events", "results", "items", "data"):
            value = payload.get(key)
            if isinstance(value, list):
                return [record for record in value if isinstance(record, dict)]
            if isinstance(value, dict):
                nested = cls._json_records(value)
                if nested:
                    return nested
        if payload.get("title") or payload.get("name"):
            return [payload]
        raise ValueError("Opportunity feed JSON contains no recognized records")

    @staticmethod
    def _json_ld_records(html: str) -> list[dict[str, Any]]:
        soup = BeautifulSoup(html, "html.parser")
        records: list[dict[str, Any]] = []
        for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
            content = script.string or script.get_text()
            if not content.strip():
                continue
            try:
                payload = json.loads(content)
            except json.JSONDecodeError as exc:
                raise ValueError("Page contains invalid JSON-LD structured data") from exc
            records.extend(BaseScraper._collect_json_ld(payload))
        if not records:
            raise ValueError(
                "Page has no supported JSON opportunity feed or schema.org Event data"
            )
        return records

    @staticmethod
    def _collect_json_ld(payload: Any) -> list[dict[str, Any]]:
        if isinstance(payload, list):
            return [
                record
                for item in payload
                for record in BaseScraper._collect_json_ld(item)
            ]
        if not isinstance(payload, dict):
            return []
        records: list[dict[str, Any]] = []
        graph = payload.get("@graph")
        if graph is not None:
            records.extend(BaseScraper._collect_json_ld(graph))
        types = payload.get("@type", [])
        if isinstance(types, str):
            types = [types]
        normalized_types = {
            item.rsplit("/", maxsplit=1)[-1].rsplit("#", maxsplit=1)[-1]
            for item in types
            if isinstance(item, str)
        }
        if normalized_types.intersection({"Event", "Hackathon", "EducationEvent"}):
            records.append(
                {
                    "title": payload.get("name"),
                    "description": payload.get("description"),
                    "url": payload.get("url"),
                    "endDate": payload.get("endDate"),
                    "type": payload.get("eventType"),
                    "category": payload.get("keywords"),
                    "required_skills": payload.get("skills", []),
                }
            )
        return records


class SourceScraper(BaseScraper):
    def scrape_configured(self, url: str) -> list[NormalizedOpportunity]:
        return self.scrape(url)
