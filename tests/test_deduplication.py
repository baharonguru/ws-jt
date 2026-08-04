from job_tracker.models import AtsProvider, Job
from job_tracker.services.deduplication import deduplicate_jobs


def make_job(source_job_id: str, title: str) -> Job:
    return Job(
        source=AtsProvider.GREENHOUSE,
        source_job_id=source_job_id,
        company="Acme",
        title=title,
        location="Berlin",
        apply_url=f"https://boards.greenhouse.io/acme/jobs/{source_job_id}",
        source_payload={},
    )


def test_deduplicate_jobs_keeps_first_occurrence() -> None:
    first_job = make_job("42", "Werkstudent Data Engineering")
    duplicate_job = make_job("42", "Werkstudent Data Engineering - updated")
    different_job = make_job("43", "Werkstudent Analytics")

    result = deduplicate_jobs([first_job, duplicate_job, different_job])

    assert result == [first_job, different_job]


def test_deduplicate_jobs_does_not_merge_ids_from_different_ats() -> None:
    lever_job = make_job("42", "Werkstudent Data Engineering").model_copy(
        update={"source": AtsProvider.LEVER}
    )
    greenhouse_job = make_job("42", "Werkstudent Data Engineering")

    result = deduplicate_jobs([lever_job, greenhouse_job])

    assert result == [lever_job, greenhouse_job]