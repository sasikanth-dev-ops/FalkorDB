from urllib.parse import urljoin

from bs4 import BeautifulSoup
from requests import Response

from scrapers.base_scraper import SourceScraper


class UnstopScraper(SourceScraper):
    platform = "Unstop"
    allowed_hosts = ("unstop.com", "www.unstop.com")
    default_type = "Opportunity"

    def parse_response(self, response: Response) -> list[dict[str, object]]:
        content_type = response.headers.get("Content-Type", "").casefold()
        if "json" in content_type:
            return super().parse_response(response)

        try:
            return super().parse_response(response)
        except ValueError:
            soup = BeautifulSoup(response.text, "html.parser")
            records: list[dict[str, object]] = []

            # Look for competition, hackathon, and opportunity links
            for anchor in soup.find_all("a", href=True):
                href = str(anchor["href"])
                if not any(
                    segment in href
                    for segment in (
                        "/competitions/",
                        "/hackathons/",
                        "/internships/",
                        "/jobs/",
                        "/workshops/",
                    )
                ):
                    continue

                title_el = anchor.find(["h2", "h3", "h4", "h5", "strong"])
                title = (
                    title_el.get_text(" ", strip=True)
                    if title_el
                    else anchor.get_text(" ", strip=True)
                )

                if not title or len(title) < 4:
                    continue

                desc_el = anchor.find("p") or anchor.find("span")
                desc = desc_el.get_text(" ", strip=True) if desc_el else title

                category = "Hackathon" if "/hackathons/" in href else "Opportunity"

                records.append(
                    {
                        "title": title,
                        "url": urljoin(response.url, href),
                        "description": desc,
                        "category": category,
                    }
                )

            # Deduplicate by url
            seen_urls = set()
            deduped = []
            for record in records:
                url = record["url"]
                if url not in seen_urls:
                    seen_urls.add(url)
                    deduped.append(record)

            if not deduped:
                raise ValueError("Could not parse Unstop opportunities from HTML or JSON-LD")

            return deduped
