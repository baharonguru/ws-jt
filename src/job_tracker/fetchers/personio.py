from typing import Any

from defusedxml import ElementTree

from job_tracker.fetchers.base import BaseFetcher, FetcherError
from job_tracker.models import AtsProvider, Job


class PersonioFetcher(BaseFetcher):
    provider = AtsProvider.PERSONIO

    def fetch(self) -> list[Job]:
        url = f"https://{self.company}.jobs.personio.de/xml"
        xml_text = self._get_text(url, params={"language": "en"})

        try:
            root = ElementTree.fromstring(xml_text)
        except ElementTree.ParseError as exc:
            raise FetcherError("personio: invalid XML response") from exc

        jobs: list[Job] = []

        for position in root.findall(".//position"):
            source_payload = self._position_to_payload(position)
            description = "\n\n".join(
                value
                for value in (
                    child_text(description_node, "value")
                    for description_node in position.findall(".//jobDescription")
                )
                if value
            )

            job = self._make_job(
                source_job_id=child_text(position, "id") or "",
                title=child_text(position, "name") or "",
                location=child_text(position, "office") or "Unknown",
                apply_url=(
                    child_text(position, "applicationUrl")
                    or f"https://{self.company}.jobs.personio.de/job/{child_text(position, 'id')}"
                ),
                description=description or None,
                posted_at=child_text(position, "createdAt"),
                source_payload=source_payload,
            )
            if job is not None:
                jobs.append(job)

        return jobs

    @staticmethod
    def _position_to_payload(position: Any) -> dict[str, str]:
        """Keep a small raw-data snapshot without coupling to XML objects."""
        return {
            local_name(element.tag): (element.text or "").strip()
            for element in position.iter()
            if len(element) == 0 and (element.text or "").strip()
        }


def local_name(tag: str) -> str:
    return tag.rsplit("}", maxsplit=1)[-1]


def child_text(element: Any, name: str) -> str | None:
    for child in element:
        if local_name(child.tag) == name and child.text:
            return child.text.strip()
    return None