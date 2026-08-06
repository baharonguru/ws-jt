import logging
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from typing import Protocol

from job_tracker.fetchers.base import BaseFetcher, FetcherError
from job_tracker.models import Job
from job_tracker.services.deduplication import deduplicate_jobs
from job_tracker.services.matching import JobFilterCriteria, filter_matching_jobs

logger = logging.getLogger(__name__)


class JobStore(Protocol):
    """The persistence operations required by the pipeline."""

    def save_all_if_new(self, jobs: Iterable[Job]) -> Sequence[object]: ...


@dataclass(frozen=True)
class PipelineFailure:
    provider: str
    company: str
    error: str


@dataclass(frozen=True)
class PipelineResult:
    fetched_count: int
    matching_count: int
    deduplicated_count: int
    new_count: int
    failures: tuple[PipelineFailure, ...]


def run_pipeline(
    fetchers: Iterable[BaseFetcher],
    job_store: JobStore,
    criteria: JobFilterCriteria | None = None,
) -> PipelineResult:
    """Fetch, filter, deduplicate, and persist jobs in one sequential run."""
    fetched_jobs: list[Job] = []
    failures: list[PipelineFailure] = []

    for fetcher in fetchers:
        try:
            jobs = fetcher.fetch()
        except FetcherError as exc:
            logger.warning("Fetch failed for %s/%s: %s", fetcher.provider, fetcher.company, exc)
            failures.append(
                PipelineFailure(
                    provider=fetcher.provider.value,
                    company=fetcher.company,
                    error=str(exc),
                )
            )
            continue
        except Exception as exc:
            logger.exception(
                "Unexpected fetch failure for %s/%s",
                fetcher.provider,
                fetcher.company,
            )
            failures.append(
                PipelineFailure(
                    provider=fetcher.provider.value,
                    company=fetcher.company,
                    error=str(exc),
                )
            )
            continue

        fetched_jobs.extend(jobs)

    matching_jobs = filter_matching_jobs(fetched_jobs, criteria)
    unique_jobs = deduplicate_jobs(matching_jobs)
    new_records = job_store.save_all_if_new(unique_jobs)

    return PipelineResult(
        fetched_count=len(fetched_jobs),
        matching_count=len(matching_jobs),
        deduplicated_count=len(unique_jobs),
        new_count=len(new_records),
        failures=tuple(failures),
    )
