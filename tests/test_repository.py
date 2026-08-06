from uuid import uuid4

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from job_tracker.db import JobRecord, JobRepository, get_engine
from job_tracker.models import AtsProvider, Job


def make_job() -> Job:
    return Job(
        source=AtsProvider.LEVER,
        source_job_id=f"repository-test-{uuid4()}",
        company="Acme",
        title="Werkstudent Data Engineering",
        location="Leipzig, Germany",
        apply_url="https://jobs.lever.co/acme/test-job",
        source_payload={"id": "test-job"},
    )


@pytest.mark.integration
def test_repository_inserts_a_job_only_once() -> None:
    session = Session(get_engine())
    job = make_job()

    try:
        repository = JobRepository(session)

        first_record = repository.save_if_new(job)
        duplicate_record = repository.save_if_new(job)
        session.flush()

        count = session.scalar(
            select(func.count())
            .select_from(JobRecord)
            .where(JobRecord.source_job_id == job.source_job_id)
        )

        assert first_record is not None
        assert duplicate_record is None
        assert first_record.title == job.title
        assert count == 1
    finally:
        session.rollback()
        session.close()
