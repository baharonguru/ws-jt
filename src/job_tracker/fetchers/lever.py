
from job_tracker.fetchers.base import BaseFetcher, FetcherError, get_mapping
from job_tracker.models import AtsProvider, Job


class LeverFetcher(BaseFetcher):
    provider = AtsProvider.LEVER

    def fetch(self) -> list[Job]:
        url = f"https://api.lever.co/v0/postings/{self.company}"
        payload = self._get_json(url, params={"mode": "json"})

        if not isinstance(payload, list):
            raise FetcherError("lever: expected a JSON list of job postings")

        jobs: list[Job] = []

        for item in payload:
            if not isinstance(item, dict):
                continue

            categories = get_mapping(item.get("categories"))
            job = self._make_job(
                source_job_id=item.get("id", ""),
                title=item.get("text", ""),
                location=categories.get("location", "Unknown"),
                apply_url=item.get("hostedUrl") or item.get("applyUrl", ""),
                description=item.get("descriptionPlain") or item.get("description"),
                posted_at=item.get("createdAt"),
                source_payload=item,
            )
            if job is not None:
                jobs.append(job)

        return jobs