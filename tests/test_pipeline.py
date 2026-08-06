from collections.abc import Iterable, Sequence

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
        if self.error is not None:
            raise self.error
        return self.jobs


class FakeJobStore:
    def __init__(self) -> None:
        self.saved_jobs: list[Job] = []

    def save_all_if_new(self, jobs: Iterable[Job]) -> Sequence[object]:
        self.saved_jobs = list(jobs)
        return self.saved_jobs


def make_job(
    source_job_id: str,
    *,
    title: str = "Werkstudent Data Engineering",
    location: str = "Leipzig, Germany",
) -> Job:
    return Job(
        source=AtsProvider.LEVER,
        source_job_id=source_job_id,
        company="Acme",
        title=title,
        location=location,
        apply_url=f"https://jobs.lever.co/acme/{source_job_id}",
        source_payload={},
    )


def test_pipeline_filters_deduplicates_and_stores_new_jobs() -> None:
    matching_job = make_job("job-1")
    duplicate_job = make_job("job-1")
    non_matching_job = make_job("job-2", title="Senior Data Engineer")
    job_store = FakeJobStore()

    result = run_pipeline(
        [
            StubFetcher(AtsProvider.LEVER, "acme", [matching_job, duplicate_job]),
            StubFetcher(AtsProvider.GREENHOUSE, "acme", [non_matching_job]),
        ],
        job_store,
    )

    assert result.fetched_count == 3
    assert result.matching_count == 2
    assert result.deduplicated_count == 1
    assert result.new_count == 1
    assert result.failures == ()
    assert job_store.saved_jobs == [matching_job]


def test_pipeline_continues_when_one_source_fails() -> None:
    job_store = FakeJobStore()
    matching_job = make_job("job-1")

    result = run_pipeline(
        [
            StubFetcher(AtsProvider.LEVER, "broken", error=FetcherError("network unavailable")),
            StubFetcher(AtsProvider.GREENHOUSE, "acme", [matching_job]),
        ],
        job_store,
    )

    assert result.new_count == 1
    assert len(result.failures) == 1
    assert result.failures[0].company == "broken"
