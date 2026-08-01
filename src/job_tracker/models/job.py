from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field


class AtsProvider(StrEnum):
    LEVER = "lever"
    GREENHOUSE = "greenhouse"
    PERSONIO = "personio"
    SMARTRECRUITERS = "smartrecruiters"


class Job(BaseModel):
    """The one schema every ATS fetcher must produce."""

    model_config = ConfigDict(extra="forbid")

    source: AtsProvider
    source_job_id: str = Field(min_length=1)
    company: str = Field(min_length=1)
    title: str = Field(min_length=1)
    location: str = "Unknown"
    description: str | None = None
    apply_url: AnyHttpUrl
    posted_at: datetime | None = None
    fetched_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    source_payload: dict[str, Any] = Field(repr=False)