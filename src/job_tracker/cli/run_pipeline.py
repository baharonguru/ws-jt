import argparse
import logging
from pathlib import Path

from job_tracker.config import get_settings
from job_tracker.db import JobRepository, session_scope
from job_tracker.fetchers import build_fetcher
from job_tracker.pipeline import PipelineResult, run_pipeline
from job_tracker.source_config import SourceConfigurationError, load_source_configs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the job tracker once.")
    parser.add_argument(
        "--sources",
        type=Path,
        default=Path("config/sources.json"),
        help="Path to local ATS source configuration.",
    )
    return parser.parse_args()


def print_results(result: PipelineResult) -> None:
    new_keys = {(job.source, job.source_job_id) for job in result.new_jobs}

    print("\n=== Job Tracker Results ===")
    print(
        f"Fetched: {result.fetched_count} | "
        f"Matching: {result.matching_count} | "
        f"New: {result.new_count} | "
        f"Failed sources: {len(result.failures)}"
    )

    if not result.matching_jobs:
        print("\nNo matching CS student jobs found.")
    else:
        print("\nMatching jobs (remote → Leipzig → Berlin):")
        for job in result.matching_jobs:
            status = "NEW" if (job.source, job.source_job_id) in new_keys else "known"
            print(f"\n[{status}] {job.title}")
            print(f"Company: {job.company} | Location: {job.location}")
            print(f"Source: {job.source.value} | Apply: {job.apply_url}")

    if result.failures:
        print("\nFailed sources:")
        for failure in result.failures:
            print(f"- {failure.provider}/{failure.company}: {failure.error}")


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
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

    print_results(result)
    return 1 if result.failures else 0


if __name__ == "__main__":
    raise SystemExit(main())