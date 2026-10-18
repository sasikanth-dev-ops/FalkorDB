import re
from datetime import date, datetime
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from requests import Response

from scrapers.base_scraper import SourceScraper


def _listing_deadline(date_text: str, today: date) -> str | None:
    normalized = re.sub(r"[\u2010-\u2015\u2212\ufffd]", "-", date_text)
    date_range = re.search(
        r"\b([A-Za-z]{3,9})\s+(\d{1,2})\s*-\s*"
        r"(?:(?P<end_month>[A-Za-z]{3,9})\s+)?(?P<end_day>\d{1,2})\b",
        normalized,
    )
    if date_range:
        month_text = date_range.group("end_month") or date_range.group(1)
        day = int(date_range.group("end_day"))
    else:
        single_date = re.search(r"\b([A-Za-z]{3,9})\s+(\d{1,2})\b", normalized)
        if not single_date:
            return None
        month_text = single_date.group(1)
        day = int(single_date.group(2))

    month = None
    for month_format in ("%b", "%B"):
        try:
            month = datetime.strptime(month_text, month_format).month
            break
        except ValueError:
            continue
    if month is None:
        return None

    try:
        deadline = date(today.year, month, day)
    except ValueError:
        return None
    if (today - deadline).days > 183:
        deadline = date(today.year + 1, month, day)
    return deadline.isoformat()


class WeMakeDevsScraper(SourceScraper):
    platform = "WeMakeDevs"
    allowed_hosts = ("wemakedevs.org", "wemakedevs.com")
    default_type = "Hackathon"

    def parse_response(self, response: Response) -> list[dict[str, object]]:
        content_type = response.headers.get("Content-Type", "").casefold()
        if "json" in content_type:
            return super().parse_response(response)

        try:
            return super().parse_response(response)
        except ValueError:
            soup = BeautifulSoup(response.text, "html.parser")
            records = []
            for anchor in soup.find_all("a", href=True):
                href = anchor["href"]
                if not isinstance(href, str) or not href.startswith("/hackathons/"):
                    continue

                title_element = anchor.find(["h1", "h2", "h3", "h4"])
                title = (
                    title_element.get_text(" ", strip=True)
                    if title_element
                    else anchor.get_text(" ", strip=True)
                )
                if not title:
                    continue

                card_text = anchor.get_text(" ", strip=True)
                date_element = anchor.find_all("span")
                deadline = (
                    _listing_deadline(
                        date_element[1].get_text(" ", strip=True), date.today()
                    )
                    if len(date_element) > 1
                    else None
                )

                description_element = anchor.find("p")
                normalized_title = title.casefold()
                opportunity_type = (
                    "Event"
                    if "mixer" in normalized_title
                    else "OpenSource"
                    if "open source" in normalized_title
                    else "Hackathon"
                )
                records.append(
                    {
                        "title": title,
                        "url": urljoin(response.url, href),
                        "type": opportunity_type,
                        "deadline": deadline,
                        "description": (
                            description_element.get_text(" ", strip=True)
                            if description_element
                            else card_text
                        ),
                        "category": "Hackathon",
                    }
                )
            if not records:
                raise
            return records
