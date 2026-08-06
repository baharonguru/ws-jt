import json
from pathlib import Path

from pydantic import BaseModel, Field, TypeAdapter, ValidationError, field_validator

from job_tracker.models import AtsProvider


class SourceConfigurationError(ValueError):
    """Raised when the local ATS source configuration is invalid."""


class SourceConfig(BaseModel):
    """One company board to fetch from a supported ATS provider."""

    provider: AtsProvider
    company: str = Field(min_length=1)

    @field_validator("company")
    @classmethod
    def company_must_not_be_blank(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("company must not be blank")
        return normalized


def load_source_configs(path: Path) -> list[SourceConfig]:
    """Load and validate a JSON list of ATS company board configurations."""
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return TypeAdapter(list[SourceConfig]).validate_python(payload)
    except (OSError, json.JSONDecodeError, ValidationError) as exc:
        raise SourceConfigurationError(
            f"Could not load source configuration at {path}: {exc}"
        ) from exc
