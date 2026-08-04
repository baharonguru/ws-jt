from job_tracker.fetchers.smartrecruiters import SmartRecruitersFetcher
from tests.fakes import FakeResponse, FakeSession


def test_smartrecruiters_fetcher_sends_api_key_and_normalizes_job() -> None:
    session = FakeSession(
        FakeResponse(
            json_data={
                "content": [
                    {
                        "id": "smart-5",
                        "name": "Werkstudent Platform Engineering",
                        "ref": "https://jobs.smartrecruiters.com/acme/smart-5",
                        "releasedDate": "2026-07-31T10:00:00Z",
                        "location": {
                            "city": "Berlin",
                            "country": "Germany",
                        },
                    }
                ]
            }
        )
    )

    jobs = SmartRecruitersFetcher(
        company="acme",
        api_key="test-key",
        session=session,
    ).fetch()

    assert len(jobs) == 1
    assert jobs[0].location == "Berlin, Germany"
    assert session.calls[0]["headers"] == {"X-SmartToken": "test-key"}
    assert session.calls[0]["params"] == {"limit": 100, "offset": 0}