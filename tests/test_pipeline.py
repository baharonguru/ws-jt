from collections.abc import Iterable

from job_tracker.fetchers.base import FetcherError
from job_tracker.models import AtsProvider, Job
from job_tracker.pipeline import run_pipeline


class StubFetcher:
    def __init__(
        self,
        provider: AtsProvider,
        company: str,
        jobs: list[Job] | None = None,
        error: Exception | None = None,
    ) -> None:
        self.provider = provider
        self.company = company
        self.jobs = jobs or []
        self.error = error

    def fetch(self) -> list[Job]:
        if self.error:
            raise self.error
        return self.jobs


class FakeJobStore:
    def __init__(self) -> None:
        self.saved_jobs: list[Job] = []

    def save_if_new(self, job: Job) -> object | None:
        if job in self.saved_jobs:
            return None
        self.saved_jobs.append(job)
        return object()


def make_job(source_job_id: str, title: str = "Werkstudent Data Engineering") -> Job:
    return Job(
        source=AtsProvider.LEVER,
        source_job_id=source_job_id,
        company="Acme",
        title=title,
        location="Leipzig, Germany",
        apply_url=f"https://jobs.lever.co/acme/{source_job_id}",
        source_payload={},
    )


def test_pipeline_filters_deduplicates_and_stores_new_jobs() -> None:
    matching = make_job("job-1")
    duplicate = make_job("job-1")
    irrelevant = make_job("job-2", "Werkstudent Marketing")
    store = FakeJobStore()

    result = run_pipeline(
        [
            StubFetcher(AtsProvider.LEVER, "acme", [matching, duplicate]),
            StubFetcher(AtsProvider.GREENHOUSE, "acme", [irrelevant]),
        ],
        store,
    )

    assert result.fetched_count == 3
    assert result.matching_count == 1
    assert result.new_count == 1
    assert result.new_jobs == (matching,)


def test_pipeline_continues_when_a_source_fails() -> None:
    store = FakeJobStore()
    matching = make_job("job-1")

    result = run_pipeline(
        [
            StubFetcher(AtsProvider.LEVER, "broken", error=FetcherError("unavailable")),
            StubFetcher(AtsProvider.GREENHOUSE, "acme", [matching]),
        ],
        store,
    )

    assert result.new_count == 1
    assert len(result.failures) == 1
    assert result.failures[0].company == "broken"