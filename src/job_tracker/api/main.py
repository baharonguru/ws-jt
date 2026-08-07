from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import Depends, FastAPI, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from job_tracker.db import JobRepository, get_db_session
from job_tracker.models import AtsProvider

app = FastAPI(
    title="Werkstudent Job Tracker API",
    version="0.1.0",
    description="Search tracked computer-science student jobs.",
)

SessionDependency = Annotated[Session, Depends(get_db_session)]


class JobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    source: str
    source_job_id: str
    company: str
    title: str
    location: str
    description: str | None
    apply_url: str
    posted_at: datetime | None
    first_seen_at: datetime


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/jobs", response_model=list[JobResponse])
def list_jobs(
    session: SessionDependency,
    q: str | None = Query(default=None, max_length=100),
    location: str | None = Query(default=None, max_length=100),
    source: AtsProvider | None = None,
    limit: int = Query(default=50, ge=1, le=100),
) -> list[JobResponse]:
    repository = JobRepository(session)
    return repository.list_jobs(
        query=q,
        location=location,
        source=source,
        limit=limit,
    )