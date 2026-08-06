from collections.abc import Iterable

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from job_tracker.db.models import JobRecord
from job_tracker.models import Job


class JobRepository:
    """Database operations for tracked job listings."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def save_if_new(self, job: Job) -> JobRecord | None:
        """
        Insert a job only when its ATS source and source ID have not been seen.

        PostgreSQL performs this atomically, so a concurrent pipeline run cannot
        create a duplicate listing.
        """
        statement = (
            insert(JobRecord)
            .values(
                source=job.source.value,
                source_job_id=job.source_job_id,
                company=job.company,
                title=job.title,
                location=job.location,
                description=job.description,
                apply_url=str(job.apply_url),
                posted_at=job.posted_at,
                raw_payload=job.source_payload,
            )
            .on_conflict_do_nothing(constraint="uq_jobs_source_source_job_id")
            .returning(JobRecord.id)
        )

        record_id = self.session.execute(statement).scalar_one_or_none()
        return self.session.get(JobRecord, record_id) if record_id is not None else None

    def save_all_if_new(self, jobs: Iterable[Job]) -> list[JobRecord]:
        """Store a sequence of jobs and return only the records newly inserted."""
        return [record for job in jobs if (record := self.save_if_new(job)) is not None]
