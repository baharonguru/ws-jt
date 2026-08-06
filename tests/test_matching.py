from job_tracker.models import AtsProvider, Job
from job_tracker.services.matching import JobFilterCriteria, filter_matching_jobs


def make_job(
    *,
    title: str = "Werkstudent Data Engineering",
    location: str = "Berlin, Germany",
    description: str | None = None,
) -> Job:
    return Job(
        source=AtsProvider.LEVER,
        source_job_id="job-1",
        company="Acme",
        title=title,
        location=location,
        description=description,
        apply_url="https://jobs.lever.co/acme/job-1",
        source_payload={},
    )


def test_filter_keeps_werkstudent_job_in_berlin() -> None:
    jobs = [make_job()]

    result = filter_matching_jobs(jobs)

    assert result == jobs


def test_filter_matches_keyword_in_description() -> None:
    job = make_job(
        title="Data Engineering Intern",
        description="We are looking for a Werkstudent.",
    )

    result = filter_matching_jobs([job])

    assert result == [job]


def test_filter_rejects_job_without_target_role() -> None:
    job = make_job(title="Senior Data Engineer")

    result = filter_matching_jobs([job])

    assert result == []


def test_filter_rejects_non_technical_werkstudent_role() -> None:
    job = make_job(title="Werkstudent Marketing", location="Leipzig, Germany")

    result = filter_matching_jobs([job])

    assert result == []


def test_filter_rejects_job_outside_target_location() -> None:
    job = make_job(location="Munich, Germany")

    result = filter_matching_jobs([job])

    assert result == []


def test_filter_keeps_remote_job_outside_preferred_cities() -> None:
    job = make_job(
        location="Munich, Germany",
        description="This Werkstudent position is fully remote within Germany.",
    )

    result = filter_matching_jobs([job])

    assert result == [job]


def test_filter_orders_remote_then_leipzig_then_berlin() -> None:
    berlin_job = make_job(location="Berlin, Germany")
    leipzig_job = make_job(location="Leipzig, Germany")
    remote_job = make_job(
        location="Hamburg, Germany",
        description="Remote work is possible.",
    )

    result = filter_matching_jobs([berlin_job, leipzig_job, remote_job])

    assert result == [remote_job, leipzig_job, berlin_job]


def test_custom_criteria_can_match_praktikum() -> None:
    job = make_job(title="Praktikum Data Engineering")

    criteria = JobFilterCriteria(
        role_keywords=("praktikum",),
        preferred_location_keywords=("berlin",),
    )

    result = filter_matching_jobs([job], criteria)

    assert result == [job]
