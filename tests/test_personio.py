from job_tracker.fetchers.personio import PersonioFetcher
from tests.fakes import FakeResponse, FakeSession


def test_personio_fetcher_normalizes_xml() -> None:
    xml = """
    <workzag-jobs>
      <position>
        <id>personio-7</id>
        <name>Werkstudent Data Analytics</name>
        <office>Berlin</office>
        <createdAt>2026-07-31T10:00:00Z</createdAt>
        <applicationUrl>https://acme.jobs.personio.de/job/personio-7</applicationUrl>
        <jobDescriptions>
          <jobDescription>
            <name>Job description</name>
            <value>Support our analytics team.</value>
          </jobDescription>
        </jobDescriptions>
      </position>
    </workzag-jobs>
    """
    session = FakeSession(FakeResponse(text=xml))

    jobs = PersonioFetcher(company="acme", session=session).fetch()

    assert len(jobs) == 1
    assert jobs[0].title == "Werkstudent Data Analytics"
    assert jobs[0].location == "Berlin"
    assert jobs[0].source_job_id == "personio-7"
    assert "analytics team" in jobs[0].description
    assert session.calls[0]["params"] == {"language": "en"}