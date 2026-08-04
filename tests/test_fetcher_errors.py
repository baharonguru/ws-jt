import pytest

from job_tracker.fetchers.base import FetcherError
from job_tracker.fetchers.lever import LeverFetcher
from tests.fakes import FakeResponse, FakeSession


def test_fetcher_raises_clear_error_for_http_failure() -> None:
    session = FakeSession(FakeResponse(status_code=503))

    with pytest.raises(FetcherError, match="request failed"):
        LeverFetcher(company="acme", session=session).fetch()


def test_fetcher_rejects_an_invalid_top_level_lever_payload() -> None:
    session = FakeSession(FakeResponse(json_data={"not": "a list"}))

    with pytest.raises(FetcherError, match="expected a JSON list"):
        LeverFetcher(company="acme", session=session).fetch()