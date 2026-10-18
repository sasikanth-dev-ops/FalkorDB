from typing import Any

from requests import Response

from scrapers.base_scraper import SourceScraper


class GitHubBountiesScraper(SourceScraper):
    platform = "GitHub"
    allowed_hosts = ("github.com", "github.io", "api.github.com")
    default_type = "OpenSource"

    def parse_response(self, response: Response) -> list[dict[str, Any]]:
        content_type = response.headers.get("Content-Type", "").casefold()
        if "json" not in content_type:
            return super().parse_response(response)

        records = self._json_records(response.json())
        return [
            {
                "title": record.get("title"),
                "url": record.get("html_url") or record.get("url"),
                "description": record.get("body"),
                "category": ", ".join(
                    label["name"]
                    for label in record.get("labels", [])
                    if isinstance(label, dict) and isinstance(label.get("name"), str)
                )[:100],
            }
            for record in records
        ]
