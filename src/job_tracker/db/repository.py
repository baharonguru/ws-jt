from collections.abc import Iterable

from sqlalchemy import or_, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from job_tracker.db.models import JobRecord
from job_tracker.models import AtsProvider, Job


class JobRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def save_if_new(self, job: Job) -> JobRecord | None:
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
        return [record for job in jobs if (record := self.save_if_new(job)) is not None]

    def list_jobs(
        self,
        *,
        query: str | None = None,
        location: str | None = None,
        source: AtsProvider | None = None,
        limit: int = 50,
    ) -> list[JobRecord]:
        statement = select(JobRecord).order_by(JobRecord.first_seen_at.desc()).limit(limit)

        if query:
            pattern = f"%{query.strip()}%"
            statement = statement.where(
                or_(
                    JobRecord.title.ilike(pattern),
                    JobRecord.company.ilike(pattern),
                    JobRecord.description.ilike(pattern),
                )
            )

        if location:
            statement = statement.where(JobRecord.location.ilike(f"%{location.strip()}%"))

        if source:
            statement = statement.where(JobRecord.source == source.value)

        return list(self.session.scalars(statement))