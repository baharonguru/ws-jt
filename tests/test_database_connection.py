import pytest
from sqlalchemy import text

from job_tracker.db import get_engine


@pytest.mark.integration
def test_postgres_connection() -> None:
    with get_engine().connect() as connection:
        result = connection.execute(text("SELECT 1")).scalar_one()

    assert result == 1