from dataclasses import dataclass

from backend.config.env import Settings
from backend.models.ingestion import ScrapeSource
from scrapers.base_scraper import SourceScraper
from scrapers.github_bounties_scraper import GitHubBountiesScraper
from scrapers.normalizer import NormalizedOpportunity
from scrapers.unstop_scraper import UnstopScraper
from scrapers.wemakedevs_scraper import WeMakeDevsScraper

DEFAULT_WEMAKEDEVS_URL = "https://www.wemakedevs.org/hackathons"


@dataclass(frozen=True)
class ConfiguredSource:
    source: ScrapeSource
    url: str
    scraper: SourceScraper


def configured_sources(
    settings: Settings, requested: list[ScrapeSource] | None = None
) -> list[ConfiguredSource]:
    definitions = {
        ScrapeSource.unstop: (settings.unstop_scrape_url, UnstopScraper),
        ScrapeSource.wemakedevs: (
            settings.wemakedevs_scrape_url or DEFAULT_WEMAKEDEVS_URL,
            WeMakeDevsScraper,
        ),
        ScrapeSource.github_bounties: (
            settings.github_bounties_scrape_url,
            GitHubBountiesScraper,
        ),
    }
    selected = requested or list(ScrapeSource)
    sources = []
    for source in selected:
        url, scraper_type = definitions[source]
        if not url:
            raise ValueError(
                f"No URL configured for {source.value}; set its *_SCRAPE_URL variable"
            )
        sources.append(ConfiguredSource(source, url, scraper_type()))
    return sources


def scrape_configured_sources(
    sources: list[ConfiguredSource],
) -> list[tuple[ScrapeSource, list[NormalizedOpportunity]]]:
    return [
        (source.source, source.scraper.scrape(source.url))
        for source in sources
    ]
