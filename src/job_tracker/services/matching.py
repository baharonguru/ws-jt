from collections.abc import Iterable

from pydantic import BaseModel, field_validator

from job_tracker.models import Job


class JobFilterCriteria(BaseModel):
    """The rules used to decide whether a job is worth tracking."""

    role_keywords: tuple[str, ...] = ("werkstudent",)
    preferred_location_keywords: tuple[str, ...] = ("leipzig", "berlin")
    remote_keywords: tuple[str, ...] = ("fully remote", "remote", "homeoffice", "home office")

    @field_validator(
        "role_keywords",
        "preferred_location_keywords",
        "remote_keywords",
    )
    @classmethod
    def keywords_must_not_be_empty(
        cls,
        keywords: tuple[str, ...],
    ) -> tuple[str, ...]:
        normalized = tuple(keyword.strip() for keyword in keywords if keyword.strip())

        if not normalized:
            raise ValueError("At least one non-empty keyword is required")

        return normalized


def filter_matching_jobs(
    jobs: Iterable[Job],
    criteria: JobFilterCriteria | None = None,
) -> list[Job]:
    """
    Return matching jobs ordered by the user's preference.

    A role keyword may appear in the title or description.
    A job is eligible when it is remote, or when its location is Leipzig or Berlin.
    Results are ordered: remote, Leipzig, then Berlin.
    """
    active_criteria = criteria or JobFilterCriteria()

    matching_jobs = [
        job
        for job in jobs
        if matches_job(job, active_criteria)
    ]
    return sorted(
        matching_jobs,
        key=lambda job: job_preference_score(job, active_criteria),
    )


def matches_job(job: Job, criteria: JobFilterCriteria) -> bool:
    searchable_job_text = " ".join(
        part
        for part in (job.title, job.description)
        if part
    )

    remote_searchable_text = f"{job.location} {searchable_job_text}"

    return contains_any(searchable_job_text, criteria.role_keywords) and (
        contains_any(remote_searchable_text, criteria.remote_keywords)
        or contains_any(job.location, criteria.preferred_location_keywords)
    )


def job_preference_score(job: Job, criteria: JobFilterCriteria) -> int:
    """Return a lower number for a more desirable matching job."""
    searchable_text = " ".join(part for part in (job.title, job.description) if part)

    if contains_any(f"{job.location} {searchable_text}", criteria.remote_keywords):
        return 0

    for score, location in enumerate(criteria.preferred_location_keywords, start=1):
        if location.casefold() in job.location.casefold():
            return score

    # This is defensive: matches_job() should already have ruled this out.
    return len(criteria.preferred_location_keywords) + 1


def contains_any(text: str, keywords: Iterable[str]) -> bool:
    """Case-insensitive matching that also handles German Unicode safely."""
    normalized_text = text.casefold()

    return any(keyword.casefold() in normalized_text for keyword in keywords)
