from job_tracker.config import Settings
from job_tracker.fetchers.base import BaseFetcher
from job_tracker.fetchers.greenhouse import GreenhouseFetcher
from job_tracker.fetchers.lever import LeverFetcher
from job_tracker.fetchers.personio import PersonioFetcher
from job_tracker.fetchers.smartrecruiters import SmartRecruitersFetcher
from job_tracker.models import AtsProvider
from job_tracker.source_config import SourceConfig, SourceConfigurationError


def build_fetcher(source: SourceConfig, settings: Settings) -> BaseFetcher:
    """Create the correct ATS fetcher for a validated source configuration."""
    if source.provider is AtsProvider.LEVER:
        return LeverFetcher(company=source.company)
    if source.provider is AtsProvider.GREENHOUSE:
        return GreenhouseFetcher(company=source.company)
    if source.provider is AtsProvider.PERSONIO:
        return PersonioFetcher(company=source.company)
    if source.provider is AtsProvider.SMARTRECRUITERS:
        if settings.smartrecruiters_api_key is None:
            raise SourceConfigurationError(
                "SMARTRECRUITERS_API_KEY is required for a SmartRecruiters source"
            )
        return SmartRecruitersFetcher(
            company=source.company,
            api_key=settings.smartrecruiters_api_key.get_secret_value(),
        )

    raise SourceConfigurationError(f"Unsupported ATS provider: {source.provider}")
