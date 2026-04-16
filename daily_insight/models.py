from __future__ import annotations

from typing import Literal

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field

BucketName = Literal[
    "software-engineering",
    "security",
    "ai-for-security",
    "security-for-ai",
]
TransportName = Literal["rss"]
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
