
from job_tracker.fetchers.base import BaseFetcher, FetcherError, get_mapping
from job_tracker.models import AtsProvider, Job


class GreenhouseFetcher(BaseFetcher):
    provider = AtsProvider.GREENHOUSE

    def fetch(self) -> list[Job]:
        url = f"https://boards-api.greenhouse.io/v1/boards/{self.company}/jobs"
        payload = self._get_json(url, params={"content": "true"})

        if not isinstance(payload, dict):
            raise FetcherError("greenhouse: expected a JSON object")

        raw_jobs = payload.get("jobs")
        if not isinstance(raw_jobs, list):
            raise FetcherError("greenhouse: response did not contain a jobs list")

        jobs: list[Job] = []

        for item in raw_jobs:
            if not isinstance(item, dict):
                continue

            location = get_mapping(item.get("location"))
            job = self._make_job(
                source_job_id=item.get("id", ""),
                title=item.get("title", ""),
                location=location.get("name", "Unknown"),
                apply_url=item.get("absolute_url", ""),
                description=item.get("content"),
                posted_at=item.get("updated_at"),
                source_payload=item,
            )
            if job is not None:
                jobs.append(job)

        return jobs