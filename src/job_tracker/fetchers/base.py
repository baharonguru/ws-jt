from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any, ClassVar

import requests
from pydantic import ValidationError
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from job_tracker.models import AtsProvider, Job

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT_SECONDS = 20


class FetcherError(RuntimeError):
    """Raised when a remote ATS endpoint cannot be fetched or parsed."""


class BaseFetcher(ABC):
    provider: ClassVar[AtsProvider]

    def __init__(
        self,
        company: str,
        session: requests.Session | None = None,
        timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        if not company.strip():
            raise ValueError("company must not be empty")
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")

        self.company = company.strip()
        self.session = session or self._build_session()
        self.timeout_seconds = timeout_seconds

    @staticmethod
    def _build_session() -> requests.Session:
        session = requests.Session()

        retry_policy = Retry(
            total=3,
            connect=3,
            read=3,
            status=3,
            backoff_factor=0.5,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=frozenset({"GET"}),
        )
        adapter = HTTPAdapter(max_retries=retry_policy)
        session.mount("https://", adapter)
        session.headers.update(
            {
                "Accept": "application/json, application/xml;q=0.9, text/xml;q=0.8",
                "User-Agent": "werkstudent-job-tracker/0.1",
            }
        )
        return session

    def _get_json(
        self,
        url: str,
        params: dict[str, str | int] | None = None,
        headers: dict[str, str] | None = None,
    ) -> Any:
        response = self._get(url, params=params, headers=headers)

        try:
            return response.json()
        except ValueError as exc:
            raise FetcherError(f"{self.provider}: invalid JSON returned by {url}") from exc

    def _get_text(
        self,
        url: str,
        params: dict[str, str | int] | None = None,
    ) -> str:
        return self._get(url, params=params).text

    def _get(
        self,
        url: str,
        params: dict[str, str | int] | None = None,
        headers: dict[str, str] | None = None,
    ) -> requests.Response:
        try:
            response = self.session.get(
                url,
                params=params,
                headers=headers,
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            return response
        except requests.RequestException as exc:
            raise FetcherError(f"{self.provider}: request failed for {url}: {exc}") from exc

    def _make_job(
        self,
        *,
        source_job_id: object,
        title: object,
        location: object,
        apply_url: object,
        description: object,
        posted_at: object,
        source_payload: dict[str, Any],
    ) -> Job | None:
        """Validate one record. Bad records are logged but do not kill a whole run."""
        try:
            return Job(
                source=self.provider,
                source_job_id=str(source_job_id),
                company=self.company,
                title=str(title).strip(),
                location=str(location).strip() or "Unknown",
                description=str(description).strip() if description else None,
                apply_url=str(apply_url),
                posted_at=parse_datetime(posted_at),
                source_payload=source_payload,
            )
        except (ValidationError, TypeError, ValueError) as exc:
            logger.warning(
                "Skipping invalid %s job for company=%s: %s",
                self.provider,
                self.company,
                exc,
            )
            return None

    @abstractmethod
    def fetch(self) -> list[Job]:
        """Fetch and normalize all available jobs for this company."""


def parse_datetime(value: object) -> datetime | None:
    """Convert common ATS date formats to timezone-aware Python datetimes."""
    if value is None or value == "":
        return None

    if isinstance(value, (int, float)):
        # Lever uses Unix timestamps in milliseconds.
        return datetime.fromtimestamp(value / 1000, tz=UTC)

    if isinstance(value, str):
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)

    raise ValueError(f"Unsupported datetime value: {value!r}")


def get_mapping(value: object) -> Mapping[str, Any]:
    """Avoid assuming that a third-party API always returns a JSON object."""
    return value if isinstance(value, Mapping) else {}