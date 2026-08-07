Markdown
# Werkstudent Job Tracker

A sequential data engineering pipeline that tracks computer-science student jobs from public ATS endpoints.

## What it does

1. Fetches public job listings from Lever, Greenhouse, Personio, and SmartRecruiters.
2. Validates and normalizes every listing with Pydantic.
3. Keeps only CS-relevant `Werkstudent` roles.
4. Prioritizes remote jobs, then Leipzig, then Berlin.
5. Deduplicates in memory and in PostgreSQL.
6. Prints matching jobs to the terminal.
7. Exposes saved jobs through FastAPI.
8. Runs tests with GitHub Actions.

No Python scheduler, background loop, or web scraping is used.

## Architecture

```text
Public ATS APIs/XML
  → Fetchers
  → Pydantic Job model
  → CS + location filter
  → Deduplication
  → PostgreSQL
  → CLI output / FastAPI search API
```

## Local Setup
```Bash
# 1. Set up virtual environment and install dependencies
python3 -m venv venv
source venv/bin/activate
python -m pip install -e ".[dev]"

# 2. Copy environment templates
cp .env.example .env
cp config/sources.example.json config/sources.json

# 3. Start PostgreSQL and run migrations
docker compose up -d database
python -m alembic upgrade head

# 4. Run the pipeline locally
python -m job_tracker.cli.run_pipeline
```

## Running the API
```Bash
uvicorn job_tracker.api.main:app --reload
Open http://127.0.0.1:8000/docs in your browser.

Useful endpoints:

GET /health — Check API status

GET /jobs — View all tracked jobs

GET /jobs?q=data — Search by keyword

GET /jobs?location=leipzig — Filter by location

GET /jobs?source=lever — Filter by ATS provider
```

## Testing & Code Quality
```Bash
python -m ruff check .
python -m pytest
Docker Deployment
Bash
docker compose up --build
The API will be available at http://127.0.0.1:8000/docs.
```
