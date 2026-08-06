import json
from pathlib import Path

import pytest

from job_tracker.models import AtsProvider
from job_tracker.source_config import SourceConfigurationError, load_source_configs


def test_load_source_configs_validates_supported_sources(tmp_path: Path) -> None:
    path = tmp_path / "sources.json"
    path.write_text(
        json.dumps([{"provider": "lever", "company": "acme"}]),
        encoding="utf-8",
    )

    sources = load_source_configs(path)

    assert sources[0].provider is AtsProvider.LEVER
    assert sources[0].company == "acme"


def test_load_source_configs_rejects_invalid_provider(tmp_path: Path) -> None:
    path = tmp_path / "sources.json"
    path.write_text(
        json.dumps([{"provider": "unknown", "company": "acme"}]),
        encoding="utf-8",
    )

    with pytest.raises(SourceConfigurationError, match="Could not load source configuration"):
        load_source_configs(path)
