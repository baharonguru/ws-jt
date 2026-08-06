import argparse
import logging
from pathlib import Path

from job_tracker.config import get_settings
from job_tracker.db import JobRepository, session_scope
from job_tracker.fetchers import build_fetcher
from job_tracker.pipeline import run_pipeline
from job_tracker.source_config import SourceConfigurationError, load_source_configs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the job tracker once.")
    parser.add_argument(
        "--sources",
        type=Path,
        default=Path("config/sources.json"),
        help="Path to the local ATS source configuration JSON file.",
    )
    return parser.parse_args()


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    args = parse_args()

    try:
        settings = get_settings()
        sources = load_source_configs(args.sources)
        fetchers = [build_fetcher(source, settings) for source in sources]
    except SourceConfigurationError as exc:
        logging.error("Pipeline configuration error: %s", exc)
        return 2

    with session_scope() as session:
        result = run_pipeline(fetchers, JobRepository(session))

    logging.info(
        "Pipeline complete: fetched=%d matching=%d unique=%d new=%d failures=%d",
        result.fetched_count,
        result.matching_count,
        result.deduplicated_count,
        result.new_count,
        len(result.failures),
    )

    for failure in result.failures:
        logging.error("Failed source %s/%s: %s", failure.provider, failure.company, failure.error)

    return 1 if result.failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
