from collections.abc import Iterable

from job_tracker.models import Job


def deduplicate_jobs(jobs: Iterable[Job]) -> list[Job]:
    """
    Remove duplicate jobs within a pipeline run.

    The first occurrence wins, preserving input order. Later, the database will
    enforce the same uniqueness rule permanently across separate pipeline runs.
    """
    seen_keys: set[tuple[str, str]] = set()
    unique_jobs: list[Job] = []

    for job in jobs:
        job_key = (job.source.value, job.source_job_id)

        if job_key in seen_keys:
            continue

        seen_keys.add(job_key)
        unique_jobs.append(job)

    return unique_jobs