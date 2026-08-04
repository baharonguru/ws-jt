from job_tracker.fetchers.greenhouse import GreenhouseFetcher
from tests.fakes import FakeResponse, FakeSession


def test_greenhouse_fetcher_normalizes_a_job() -> None:
    session = FakeSession(
        FakeResponse(
            json_data={
                "jobs": [
                    {
                        "id": 42,
                        "title": "Werkstudent Software Engineering",
                        "location": {"name": "Berlin"},
                        "absolute_url": "https://boards.greenhouse.io/acme/jobs/42",
                        "content": "<p>Build useful things.</p>",
                        "updated_at": "2026-07-31T10:00:00Z",
                    }
                ]
            }
        )
    )

    jobs = GreenhouseFetcher(company="acme", session=session).fetch()

    assert len(jobs) == 1
    assert jobs[0].source_job_id == "42"
    assert jobs[0].location == "Berlin"
    assert jobs[0].description == "<p>Build useful things.</p>"
    assert session.calls[0]["params"] == {"content": "true"}