from job_tracker.fetchers.lever import LeverFetcher
from tests.fakes import FakeResponse, FakeSession


def test_lever_fetcher_normalizes_a_job() -> None:
    session = FakeSession(
        FakeResponse(
            json_data=[
                {
                    "id": "lever-1",
                    "text": "Werkstudent Data Engineering",
                    "categories": {"location": "Berlin, Germany"},
                    "hostedUrl": "https://jobs.lever.co/acme/lever-1",
                    "descriptionPlain": "Help build data pipelines.",
                    "createdAt": 1_720_000_000_000,
                }
            ]
        )
    )

    jobs = LeverFetcher(company="acme", session=session).fetch()

    assert len(jobs) == 1
    assert jobs[0].title == "Werkstudent Data Engineering"
    assert jobs[0].location == "Berlin, Germany"
    assert jobs[0].source_job_id == "lever-1"
    assert str(jobs[0].apply_url) == "https://jobs.lever.co/acme/lever-1"
    assert session.calls[0]["params"] == {"mode": "json"}