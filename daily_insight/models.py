from __future__ import annotations

from typing import Literal

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field

BucketName = Literal[
    "software-engineering",
    "security",
    "ai-for-security",
    "security-for-ai",
]
TransportName = Literal["rss", "json"]
CatalogTransportName = Literal["rss", "json", "atom", "html", "api"]
CatalogStatus = Literal[
    "runtime-approved",
    "reviewed-candidate",
    "deferred",
    "rejected",
]
FailurePolicy = Literal["warn", "fail"]


class SourceConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    transport: TransportName
    url: AnyHttpUrl
    bucket: BucketName
    enabled: bool = True
    required_for_daily_run: bool = True
    failure_policy: FailurePolicy = "warn"
    max_items_per_source: int = Field(default=25, ge=1, le=100)


class NormalizedItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=16, max_length=16)
    source: str = Field(min_length=1)
    bucket_hint: BucketName
    title: str
    url: AnyHttpUrl
    summary: str = ""
    published_at: str | None = None
    collected_at: str
    tags: list[str] = Field(default_factory=list)


class SourceCatalogEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    bucket: BucketName
    url: AnyHttpUrl
    transport: CatalogTransportName
    catalog_status: CatalogStatus
    machine_readable: bool
    last_reviewed: str = Field(min_length=10)
    expected_signal: str = Field(min_length=1)
    review_notes: str = Field(min_length=1)


class SourceCatalog(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reviewed_at: str = Field(min_length=10)
    review_notes: str = Field(min_length=1)
    sources: list[SourceCatalogEntry]
