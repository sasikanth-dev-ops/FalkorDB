import unittest

from backend.config.env import Settings
from backend.models.ingestion import ScrapeRequest, ScrapeSource
from scrapers.service import configured_sources


class ScraperServiceTests(unittest.TestCase):
    def test_configured_sources_requires_url_for_selected_source(self) -> None:
        settings = Settings(unstop_scrape_url=None)

        with self.assertRaisesRegex(ValueError, "No URL configured for unstop"):
            configured_sources(settings, [ScrapeSource.unstop])

    def test_configured_source_selects_expected_scraper(self) -> None:
        settings = Settings(unstop_scrape_url="https://unstop.com/events")

        configured = configured_sources(settings, [ScrapeSource.unstop])

        self.assertEqual(len(configured), 1)
        self.assertEqual(configured[0].source, ScrapeSource.unstop)
        self.assertEqual(configured[0].url, "https://unstop.com/events")
        self.assertEqual(configured[0].scraper.platform, "Unstop")

    def test_wemakedevs_uses_official_listings_by_default(self) -> None:
        configured = configured_sources(
            Settings(wemakedevs_scrape_url=None), [ScrapeSource.wemakedevs]
        )

        self.assertEqual(
            configured[0].url, "https://www.wemakedevs.org/hackathons"
        )
        self.assertEqual(configured[0].scraper.platform, "WeMakeDevs")

    def test_configured_sources_all_requires_each_url(self) -> None:
        settings = Settings(
            unstop_scrape_url="https://unstop.com/events",
            wemakedevs_scrape_url="https://wemakedevs.org/events",
            github_bounties_scrape_url=None,
        )

        with self.assertRaisesRegex(ValueError, "No URL configured for github_bounties"):
            configured_sources(settings)

    def test_scrape_request_rejects_duplicate_sources(self) -> None:
        with self.assertRaisesRegex(ValueError, "only be selected once"):
            ScrapeRequest(sources=["unstop", "unstop"])


if __name__ == "__main__":
    unittest.main()
