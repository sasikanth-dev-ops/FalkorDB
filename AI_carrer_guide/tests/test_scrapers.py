import json
import unittest
from datetime import date
from unittest.mock import MagicMock, patch

import requests

from scrapers.base_scraper import BaseScraper
from scrapers.github_bounties_scraper import GitHubBountiesScraper
from scrapers.normalizer import normalize_opportunity, validate_source_url
from scrapers.unstop_scraper import UnstopScraper
from scrapers.wemakedevs_scraper import WeMakeDevsScraper, _listing_deadline


class ScraperNormalizationTests(unittest.TestCase):
    def test_wemakedevs_listing_date_ranges_normalize_the_end_date(self) -> None:
        today = date(2026, 10, 17)

        self.assertEqual(
            _listing_deadline("Oct 14–18", today),
            "2026-10-18",
        )
        self.assertEqual(
            _listing_deadline("Sep 30 – Oct 31", today),
            "2026-10-31",
        )
        self.assertEqual(
            _listing_deadline("Aug 17–23", today),
            "2026-08-23",
        )

    def test_normalizer_maps_aliases_and_makes_stable_id(self) -> None:
        raw = {
            "name": "  Global AI Hackathon ",
            "link": "https://unstop.com/hackathons/global-ai",
            "type": "Hackathon",
            "endDate": "2026-12-31T23:00:00Z",
            "description": "<p>Build an <b>AI tool</b>.</p>",
            "skills_required": ["Python", " python ", {"name": "Vector Search"}],
        }

        first = normalize_opportunity(raw, platform="Unstop")
        second = normalize_opportunity(raw, platform="Unstop")

        self.assertEqual(first.id, second.id)
        self.assertEqual(first.title, "Global AI Hackathon")
        self.assertEqual(first.deadline, "2026-12-31")
        self.assertEqual(first.description, "Build an AI tool.")
        self.assertEqual(first.required_skills, ["Python", "Vector Search"])
        self.assertEqual(str(first.url), "https://unstop.com/hackathons/global-ai")

    def test_json_ld_event_extracts_recognized_fields(self) -> None:
        response = requests.Response()
        response.status_code = 200
        response.headers["Content-Type"] = "text/html"
        response._content = b"""
        <html><script type="application/ld+json">
        {"@type":"Event","name":"Graph Challenge",
         "url":"https://unstop.com/events/graph-challenge",
         "description":"Build with graphs.","endDate":"2026-11-20"}
        </script></html>
        """

        result = UnstopScraper().parse_response(response)

        self.assertEqual(result[0]["title"], "Graph Challenge")
        self.assertEqual(result[0]["endDate"], "2026-11-20")

    def test_json_feed_supports_nested_records(self) -> None:
        response = requests.Response()
        response.status_code = 200
        response.headers["Content-Type"] = "application/json"
        response._content = json.dumps(
            {"data": {"items": [{"title": "Backend Internship"}]}}
        ).encode()

        self.assertEqual(
            BaseScraper._json_records(response.json()),
            [{"title": "Backend Internship"}],
        )

    def test_github_search_api_records_map_to_opportunities(self) -> None:
        response = requests.Response()
        response.status_code = 200
        response.headers["Content-Type"] = "application/json"
        response._content = json.dumps(
            {
                "items": [
                    {
                        "title": "Add vector search support",
                        "html_url": "https://github.com/example/project/issues/7",
                        "body": "Bounty: implement vector search.",
                        "labels": [{"name": "bounty"}, {"name": "python"}],
                    }
                ]
            }
        ).encode()

        records = GitHubBountiesScraper().parse_response(response)

        self.assertEqual(records[0]["title"], "Add vector search support")
        self.assertEqual(
            records[0]["url"], "https://github.com/example/project/issues/7"
        )
        self.assertEqual(records[0]["description"], "Bounty: implement vector search.")
        self.assertEqual(records[0]["category"], "bounty, python")

    def test_wemakedevs_hackathon_cards_extract_titles_and_links(self) -> None:
        response = requests.Response()
        response.status_code = 200
        response.url = "https://www.wemakedevs.org/hackathons"
        response.headers["Content-Type"] = "text/html"
        response._content = b"""
        <html><a href="/hackathons/falkordb">
          <span>Remote</span><h3>Graph Hacks: Building Next-Gen RAG</h3>
          <p>$20,000 across three tracks</p>
        </a></html>
        """

        records = WeMakeDevsScraper().parse_response(response)

        self.assertEqual(records[0]["title"], "Graph Hacks: Building Next-Gen RAG")
        self.assertEqual(
            records[0]["url"], "https://www.wemakedevs.org/hackathons/falkordb"
        )
        self.assertEqual(records[0]["description"], "$20,000 across three tracks")

    def test_scrape_url_rejects_non_https_and_untrusted_hosts(self) -> None:
        with self.assertRaises(ValueError):
            validate_source_url("http://unstop.com/events", ("unstop.com",))
        with self.assertRaises(ValueError):
            validate_source_url(
                "https://unstop.com.attacker.example/events", ("unstop.com",)
            )
        self.assertEqual(
            validate_source_url(
                "https://api.github.com/search/issues?q=bounty",
                GitHubBountiesScraper.allowed_hosts,
            ),
            "https://api.github.com/search/issues?q=bounty",
        )

    @patch("scrapers.base_scraper.requests.get")
    def test_scraper_does_not_follow_redirects(self, get: MagicMock) -> None:
        response = requests.Response()
        response.raw = MagicMock()
        response.status_code = 302
        response.headers["Location"] = "http://127.0.0.1/"
        get.return_value = response  # type: ignore[attr-defined]

        with self.assertRaises(ValueError):
            UnstopScraper().scrape("https://unstop.com/events")
        get.assert_called_once()
        self.assertFalse(get.call_args.kwargs["allow_redirects"])


if __name__ == "__main__":
    unittest.main()
