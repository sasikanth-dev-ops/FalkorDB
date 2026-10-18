from enum import StrEnum

from pydantic import BaseModel, Field, field_validator


class ScrapeSource(StrEnum):
    unstop = "unstop"
    wemakedevs = "wemakedevs"
    github_bounties = "github_bounties"


class ScrapeRequest(BaseModel):
    sources: list[ScrapeSource] = Field(default_factory=list, max_length=3)

    @field_validator("sources")
    @classmethod
    def validate_unique_sources(
        cls, sources: list[ScrapeSource]
    ) -> list[ScrapeSource]:
        if len(sources) != len(set(sources)):
            raise ValueError("Each scrape source may only be selected once")
        return sources


class SourceIngestionResult(BaseModel):
    source: ScrapeSource
    records: int


class ScrapeResponse(BaseModel):
    ingested: int
    sources: list[SourceIngestionResult]
