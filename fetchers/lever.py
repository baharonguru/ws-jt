import requests
from pydantic import BaseModel, HttpUrl
from typing import Optional

# 1. Define a Pydantic model to structure & validate incoming job data
class JobListing(BaseModel):
    title: str
    location: Optional[str] = "Unknown"
    url: HttpUrl
    company: str

def fetch_lever_jobs(company_slug: str) -> list[JobListing]:
    """Fetch and parse active jobs from Lever for a given company."""
    endpoint = f"https://api.lever.co/v0/postings/{company_slug}"
    
    try:
        response = requests.get(endpoint, timeout=10)
        response.raise_for_status()  # Raise an error if request failed
        raw_jobs = response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching jobs for {company_slug}: {e}")
        return []

    parsed_jobs = []
    
    for item in raw_jobs:
        title = item.get("text", "")
        # Lever nests location inside categories
        categories = item.get("categories", {})
        location = categories.get("location", "Unknown") if categories else "Unknown"
        hosted_url = item.get("hostedUrl")

        # Basic filtering logic
        if "werkstudent" in title.lower():
            job = JobListing(
                title=title,
                location=location,
                url=hosted_url,
                company=company_slug
            )
            parsed_jobs.append(job)

    return parsed_jobs

if __name__ == "__main__":
    # Test with N26 or Delivery Hero
    target_company = "n26"
    print(f"🔍 Searching for Werkstudent roles at {target_company.upper()}...")
    
    matching_jobs = fetch_lever_jobs(target_company)
    
    if matching_jobs:
        print(f"\n✅ Found {len(matching_jobs)} match(es):")
        for job in matching_jobs:
            print(f"- [{job.company}] {job.title} | Location: {job.location}")
            print(f"  Link: {job.url}\n")
    else:
        print("No matching Werkstudent positions found right now.")