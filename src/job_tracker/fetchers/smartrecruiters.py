from typing import Any

from job_tracker.fetchers.base import BaseFetcher, FetcherError, get_mapping
from job_tracker.models import AtsProvider, Job


class SmartRecruitersFetcher(BaseFetcher):
    provider = AtsProvider.SMARTRECRUITERS

    def __init__(self, company: str, api_key: str, **kwargs: Any) -> None:
        super().__init__(company, **kwargs)

        if not api_key.strip():
            raise ValueError("SmartRecruiters API key must not be empty")
        self.api_key = api_key

    def fetch(self) -> list[Job]:
        url = f"https://api.smartrecruiters.com/v1/companies/{self.company}/postings"
        payload = self._get_json(
            url,
            params={"limit": 100, "offset": 0},
            headers={"X-SmartToken": self.api_key},
        )

        if not isinstance(payload, dict):
            raise FetcherError("smartrecruiters: expected a JSON object")

        raw_jobs = payload.get("content")
        if not isinstance(raw_jobs, list):
            raise FetcherError("smartrecruiters: response did not contain a content list")

        jobs: list[Job] = []

        for item in raw_jobs:
            if not isinstance(item, dict):
                continue

            location = get_mapping(item.get("location"))
            location_text = ", ".join(
                str(part)
                for part in (
                    location.get("city"),
                    location.get("region"),
                    location.get("country"),
                )
                if part
            )

            source_job_id = item.get("id", "")
            job = self._make_job(
                source_job_id=source_job_id,
                title=item.get("name", ""),
                location=location_text or "Unknown",
                apply_url=(
                    item.get("ref")
                    or f"https://jobs.smartrecruiters.com/{self.company}/{source_job_id}"
                ),
                description=item.get("jobAd", {}).get("sections", {}).get("jobDescription"),
                posted_at=item.get("releasedDate"),
                source_payload=item,
            )
            if job is not None:
                jobs.append(job)

        return jobs