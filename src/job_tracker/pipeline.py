import logging
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Protocol

from job_tracker.fetchers.base import BaseFetcher, FetcherError
from job_tracker.models import Job
from job_tracker.services.deduplication import deduplicate_jobs
from job_tracker.services.matching import JobFilterCriteria, filter_matching_jobs

logger = logging.getLogger(__name__)


class JobStore(Protocol):
    def save_if_new(self, job: Job) -> object | None: ...


@dataclass(frozen=True)
class PipelineFailure:
    provider: str
    company: str
    error: str


@dataclass(frozen=True)
class PipelineResult:
    fetched_count: int
    matching_jobs: tuple[Job, ...]
    new_jobs: tuple[Job, ...]
    failures: tuple[PipelineFailure, ...]

    @property
    def matching_count(self) -> int:
        return len(self.matching_jobs)

    @property
    def deduplicated_count(self) -> int:
        return len(self.matching_jobs)

    @property
    def new_count(self) -> int:
        return len(self.new_jobs)


def run_pipeline(
    fetchers: Iterable[BaseFetcher],
    job_store: JobStore,
    criteria: JobFilterCriteria | None = None,
) -> PipelineResult:
    """Run one sequential ingestion pipeline; no scheduler or background loop."""
    fetched_jobs: list[Job] = []
    failures: list[PipelineFailure] = []

    for fetcher in fetchers:
        try:
            fetched_jobs.extend(fetcher.fetch())
        except FetcherError as exc:
            logger.warning("Fetch failed for %s/%s: %s", fetcher.provider, fetcher.company, exc)
            failures.append(
                PipelineFailure(fetcher.provider.value, fetcher.company, str(exc))
            )
        except Exception as exc:
            logger.exception(
                "Unexpected fetch failure for %s/%s", fetcher.provider, fetcher.company
                )
            failures.append(
                PipelineFailure(fetcher.provider.value, fetcher.company, str(exc))
            )

    matching_jobs = filter_matching_jobs(fetched_jobs, criteria)
    unique_jobs = deduplicate_jobs(matching_jobs)

    new_jobs = tuple(
        job
        for job in unique_jobs
        if job_store.save_if_new(job) is not None
    )

    return PipelineResult(
        fetched_count=len(fetched_jobs),
        matching_jobs=tuple(unique_jobs),
        new_jobs=new_jobs,
        failures=tuple(failures),
    )